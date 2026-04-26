from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Avg
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import os
import random
import string
from .forms import SolicitudVendedorForm, ProductoForm
from .infrastructure.dependencies import (
    get_registrar_solicitud_use_case,
    get_procesar_decision_use_case,
    get_listar_categorias_use_case,
    get_buscar_productos_use_case,
    get_gestionar_carrito_use_case,
    get_crear_producto_use_case,
    get_crear_producto_use_case_con_proxy,
    get_checkout_facade,
    get_producto_repo_auditado,
    get_bam_service,
    get_suscripcion_use_case,
)
from .domain.entities.vendedor import SolicitudVendedor, SolicitudEstado
from .domain.entities.venta import Carrito, CarritoItem, MetodoPago
from .domain.entities.producto import Producto
from .infrastructure.services.monitoring import BAMService
from .application.facades.registration_facade import RegistrationFacade
from .application.factories.pqrs_factory import PQRSFactory
from .application.use_cases.pqrs_use_cases import RadicarPQRSUseCase, GestionarPQRSUseCase
from .models import (
    SolicitudVendedor as SolicitudVendedorModel,
    Auditoria, PQRS as PQRSModel,
    Suscripcion, Producto as ProductoModel,
    Comprador, ComentarioProducto, Pedido, PedidoItem,
    CalificacionTransaccion, ConfiguracionSistema,
    Vendedor as VendedorModel
)

def home(request):
    return render(request, 'inicio.html')

def custom_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('dashboard_director')
        elif hasattr(request.user, 'vendedor_profile'):
            return redirect('vendedor_dashboard')
        return redirect('inicio')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
            if user.is_superuser or user.is_staff:
                return redirect('dashboard_director')
            elif hasattr(user, 'vendedor_profile'):
                return redirect('vendedor_dashboard')
            else:
                return redirect('inicio')
        else:
            messages.error(request, 'Credenciales inválidas. Por favor intente nuevamente.')
    
    return render(request, 'login.html')

def custom_logout(request):
    auth_logout(request)
    return redirect('login')

@login_required(login_url='login')
def vendedor_dashboard(request):
    if not hasattr(request.user, 'vendedor_profile'):
        messages.error(request, 'No tienes un perfil de vendedor asociado.')
        return redirect('inicio')
    
    vendedor = request.user.vendedor_profile
    suscripcion = Suscripcion.objects.filter(vendedor=vendedor).order_by('-fecha_inicio').first()
    productos = ProductoModel.objects.filter(vendedor=vendedor)
    
    context = {
        'vendedor': vendedor,
        'suscripcion': suscripcion,
        'productos': productos
    }
    return render(request, 'vendedor_dashboard.html', context)

@login_required(login_url='login')
def iniciar_pago_suscripcion(request):
    if request.method == 'POST':
        if not hasattr(request.user, 'vendedor_profile'):
            messages.error(request, 'No eres un vendedor.')
            return redirect('inicio')
            
        plan = request.POST.get('plan')
        metodo = request.POST.get('metodo_pago')
        
        request.session['suscripcion_plan'] = plan
        
        if metodo == 'LINEA':
            return redirect('pago_en_linea')
        elif metodo == 'TARJETA':
            return redirect('pago_tarjeta')
        elif metodo == 'CONSIGNACION':
            return redirect('pago_consignacion')
            
    return redirect('vendedor_dashboard')

@login_required(login_url='login')
def pago_en_linea(request):
    pedido_id = request.session.get('checkout_pedido_id')
    if pedido_id:
        precio = request.session.get('checkout_total')
        tipo = 'Compra de Productos'
    else:
        plan = request.session.get('suscripcion_plan', 'MENSUAL')
        precios = {'MENSUAL': 50000, 'SEMESTRAL': 250000, 'ANUAL': 450000}
        precio = precios.get(plan, 0)
        tipo = f'Suscripción {plan}'
    
    if request.method == 'POST':
        num_aprobacion = str(uuid.uuid4()).split('-')[0].upper()
        if pedido_id:
            return _finalizar_pago_pedido(request, pedido_id, num_aprobacion)
        else:
            plan = request.session.get('suscripcion_plan', 'MENSUAL')
            _activar_suscripcion(request.user.vendedor_profile, plan)
            messages.success(request, f'Pago aprobado. Nro de aprobación bancaria: {num_aprobacion}')
            return redirect('vendedor_dashboard')
            
    return render(request, 'pagos/en_linea.html', {'tipo': tipo, 'precio': precio})

@login_required(login_url='login')
def pago_tarjeta(request):
    pedido_id = request.session.get('checkout_pedido_id')
    if pedido_id:
        precio = request.session.get('checkout_total')
        tipo = 'Compra de Productos'
    else:
        plan = request.session.get('suscripcion_plan', 'MENSUAL')
        precios = {'MENSUAL': 50000, 'SEMESTRAL': 250000, 'ANUAL': 450000}
        precio = precios.get(plan, 0)
        tipo = f'Suscripción {plan}'
    
    if request.method == 'POST':
        if pedido_id:
            return _finalizar_pago_pedido(request, pedido_id, "TARJETA")
        else:
            plan = request.session.get('suscripcion_plan', 'MENSUAL')
            _activar_suscripcion(request.user.vendedor_profile, plan)
            messages.success(request, 'Pago con Tarjeta de Crédito procesado exitosamente.')
            return redirect('vendedor_dashboard')
            
    return render(request, 'pagos/tarjeta.html', {'tipo': tipo, 'precio': precio})

@login_required(login_url='login')
def pago_consignacion(request):
    pedido_id = request.session.get('checkout_pedido_id')
    if pedido_id:
        precio = request.session.get('checkout_total')
        tipo = 'Compra de Productos'
        identificacion = request.user.username
        nombre = f"{request.user.first_name} {request.user.last_name}"
    else:
        plan = request.session.get('suscripcion_plan', 'MENSUAL')
        precios = {'MENSUAL': 50000, 'SEMESTRAL': 250000, 'ANUAL': 450000}
        precio = precios.get(plan, 0)
        tipo = f'Suscripción {plan}'
        vendedor = request.user.vendedor_profile
        identificacion = vendedor.solicitud.numero_identificacion
        nombre = f"{vendedor.solicitud.nombres} {vendedor.solicitud.apellidos}"
    
    if request.method == 'POST':
        # Simulación de carga de archivo batch
        file_path = os.path.join(settings.BASE_DIR, 'banco_consignaciones.txt')
        with open(file_path, 'w') as f:
            f.write(f"{identificacion},PAGADO\n")
            
        with open(file_path, 'r') as f:
            linea = f.readline().strip()
            cedula, estado = linea.split(',')
            if estado == 'PAGADO' and cedula == identificacion:
                if pedido_id:
                    return _finalizar_pago_pedido(request, pedido_id, "CONSIGNACION")
                else:
                    plan = request.session.get('suscripcion_plan', 'MENSUAL')
                    _activar_suscripcion(request.user.vendedor_profile, plan)
                    messages.success(request, 'Conciliación bancaria exitosa. Suscripción activada.')
                    return redirect('vendedor_dashboard')
            
    return render(request, 'pagos/consignacion.html', {'tipo': tipo, 'precio': precio, 'identificacion': identificacion, 'nombre': nombre})

def _finalizar_pago_pedido(request, pedido_id, num_aprobacion):
    from .models import Pedido, PedidoItem, Producto
    pedido = Pedido.objects.get(id=pedido_id)
    pedido.estado = 'PAGADO'
    pedido.save()
    
    for item in pedido.items.all():
        producto = item.producto
        producto.cantidad_disponible -= item.cantidad
        producto.save()
        
    request.session['cart'] = {'items': []}
    if 'checkout_pedido_id' in request.session: del request.session['checkout_pedido_id']
    if 'checkout_total' in request.session: del request.session['checkout_total']
    
    messages.success(request, f'¡Pago exitoso! Pedido #{pedido_id} confirmado. Nro aprobación: {num_aprobacion}')
    return redirect('calificar_transaccion', pedido_id=pedido_id)

def _activar_suscripcion(vendedor, plan):
    hoy = timezone.now()
    if plan == 'MENSUAL':
        fin = hoy + timedelta(days=30)
    elif plan == 'SEMESTRAL':
        fin = hoy + timedelta(days=180)
    else:
        fin = hoy + timedelta(days=365)
        
    Suscripcion.objects.create(
        vendedor=vendedor,
        fecha_inicio=hoy,
        fecha_fin=fin,
        tipo_facturacion=plan,
        esta_activa=True
    )
    vendedor.estado = 'ACTIVA'
    vendedor.save()


def registrar_vendedor(request):
    if request.method == 'POST':
        form = SolicitudVendedorForm(request.POST, request.FILES)
        if form.is_valid():
            # Facade coordina: guardado, Factory de documentos y Chain de validación
            facade = RegistrationFacade()
            resultado = facade.process_registration(form, request.FILES)

            estado = resultado['estado']
            sol_id = resultado['solicitud_id']

            if estado == 'PENDIENTE':
                messages.success(
                    request,
                    f'✅ Solicitud #{sol_id} registrada. '
                    f'Estado: PENDIENTE — En espera de aprobación del director.'
                )
            elif estado == 'RECHAZADA':
                messages.error(
                    request,
                    f'❌ Solicitud #{sol_id} rechazada automáticamente. '
                    f'Motivo: {resultado["message"]}'
                )
            elif estado == 'DEVUELTA':
                messages.warning(
                    request,
                    f'⚠️ Solicitud #{sol_id} devuelta para revisión. '
                    f'Motivo: {resultado["message"]}'
                )

            return redirect('inicio')
    else:
        form = SolicitudVendedorForm()
    return render(request, 'registrar_vendedor.html', {'form': form})

def consultar_estado(request):
    if request.method == 'POST':
        numero_id = request.POST.get('numero_identificacion')
        try:
            solicitud = SolicitudVendedorModel.objects.filter(numero_identificacion=numero_id).order_by('-fecha_creacion').first()
            if solicitud:
                return render(request, 'consultar_estado.html', {'solicitud': solicitud, 'busqueda': True})
            else:
                messages.error(request, 'No se encontró ninguna solicitud con ese número de identificación.')
        except Exception as e:
            messages.error(request, 'Ocurrió un error consultando la solicitud.')
            
    return render(request, 'consultar_estado.html', {'busqueda': False})

def dashboard_director(request):
    query = request.GET.get('q')
    estado = request.GET.get('estado')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    solicitudes = SolicitudVendedorModel.objects.all()

    if query:
        solicitudes = solicitudes.filter(
            Q(numero_identificacion__icontains=query) | 
            Q(nombres__icontains=query) | 
            Q(apellidos__icontains=query)
        )
    
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
    
    if fecha_inicio:
        solicitudes = solicitudes.filter(fecha_creacion__date__gte=fecha_inicio)
    
    if fecha_fin:
        solicitudes = solicitudes.filter(fecha_creacion__date__lte=fecha_fin)

    # Ordenar por fecha descendente por defecto
    solicitudes = solicitudes.order_by('-fecha_creacion')

    return render(request, 'director/dashboard.html', {
        'solicitudes': solicitudes,
        'estados': SolicitudVendedorModel.ESTADO_CHOICES
    })

def detalle_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudVendedorModel, id=solicitud_id)
    return render(request, 'director/detalle_solicitud.html', {'solicitud': solicitud})

def procesar_solicitud(request, solicitud_id):
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comentarios = request.POST.get('comentarios', '')
        try:
            get_procesar_decision_use_case().execute(solicitud_id, SolicitudEstado(decision), comentarios)
            messages.success(request, 'Procesado.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('dashboard_director')

def catalog(request):
    from core.models import Categoria as CategoriaModel
    categorias = CategoriaModel.objects.all()
    
    # Punto 8: Filtros
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    subcategoria = request.GET.get('subcategoria', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    caracteristica = request.GET.get('caracteristica', '')

    productos_qs = ProductoModel.objects.all()

    if query:
        productos_qs = productos_qs.filter(nombre__icontains=query)
    if categoria_id:
        productos_qs = productos_qs.filter(categoria_id=categoria_id)
    if subcategoria:
        productos_qs = productos_qs.filter(subcategoria__icontains=subcategoria)
    if precio_min:
        productos_qs = productos_qs.filter(valor_unitario__gte=float(precio_min))
    if precio_max:
        productos_qs = productos_qs.filter(valor_unitario__lte=float(precio_max))
    if caracteristica:
        productos_qs = productos_qs.filter(caracteristicas__icontains=caracteristica)
        
    return render(request, 'catalogo.html', {
        'categorias': categorias, 
        'productos': productos_qs,
        'filtros_actuales': request.GET
    })

def add_to_cart(request, producto_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para agregar productos al carrito.')
        return redirect('login')
    
    producto = get_object_or_404(ProductoModel, id=producto_id)
    cart_data = request.session.get('cart', {'items': []})
    items = cart_data['items']

    for item in items:
        if item['producto_id'] == producto_id:
            item['cantidad'] += 1
            item['subtotal'] = item['cantidad'] * item['precio_unitario']
            request.session['cart'] = {'items': items}
            messages.success(request, f'Se añadió otra unidad de {producto.nombre}.')
            return redirect('catalog')

    primera_imagen = producto.imagenes.first()
    items.append({
        'producto_id': producto_id,
        'nombre': producto.nombre,
        'marca': producto.marca,
        'categoria': producto.categoria.nombre,
        'categoria_id': producto.categoria_id,
        'comision_pct': producto.categoria.porcentaje_comision,
        'iva_pct': producto.categoria.porcentaje_iva,
        'domicilio_base': producto.categoria.domicilio_base,
        'es_iva_incluido': producto.categoria.es_iva_incluido,
        'precio_unitario': producto.valor_unitario,
        'peso': producto.peso,
        'cantidad': 1,
        'subtotal': producto.valor_unitario,
        'imagen_url': primera_imagen.imagen.url if primera_imagen else None,
    })
    request.session['cart'] = {'items': items}
    messages.success(request, f'{producto.nombre} añadido al carrito.')
    return redirect('catalog')

def remove_from_cart(request, producto_id):
    cart_data = request.session.get('cart', {'items': []})
    cart_data['items'] = [i for i in cart_data['items'] if i['producto_id'] != producto_id]
    request.session['cart'] = cart_data
    messages.success(request, 'Producto eliminado del carrito.')
    return redirect('view_cart')

def add_to_cart_qty_inc(request, producto_id):
    cart_data = request.session.get('cart', {'items': []})
    for item in cart_data['items']:
        if item['producto_id'] == producto_id:
            item['cantidad'] += 1
            item['subtotal'] = item['cantidad'] * item['precio_unitario']
            break
    request.session['cart'] = cart_data
    return redirect('view_cart')

def add_to_cart_qty_dec(request, producto_id):
    cart_data = request.session.get('cart', {'items': []})
    for item in cart_data['items']:
        if item['producto_id'] == producto_id:
            if item['cantidad'] <= 1:
                cart_data['items'].remove(item)
            else:
                item['cantidad'] -= 1
                item['subtotal'] = item['cantidad'] * item['precio_unitario']
            break
    request.session['cart'] = cart_data
    return redirect('view_cart')

def view_cart(request):
    cart_data = request.session.get('cart', {'items': []})
    items = cart_data['items']
    config = ConfiguracionSistema.get_config()

    subtotal = sum(i['subtotal'] for i in items)
    comision = sum(i['subtotal'] * (i.get('comision_pct', 0) / 100) for i in items)
    iva = sum(
        i['subtotal'] * i.get('iva_pct', 0)
        for i in items
        if not i.get('es_iva_incluido', True)
    )
    peso_total = sum(i.get('peso', 0) * i['cantidad'] for i in items)
    
    # Domicilio: Base (máxima de las categorías en el carrito) + factor por peso
    base_domicilio = max([i.get('domicilio_base', 0) for i in items]) if items else 0
    costo_domicilio = base_domicilio + (peso_total * config.costo_domicilio_por_kg)

    totales = {
        'subtotal': subtotal,
        'comision': comision,
        'iva': iva,
        'costo_domicilio': costo_domicilio,
        'total_sin_domicilio': subtotal + comision + iva,
        'total_con_domicilio': subtotal + comision + iva + costo_domicilio,
    }
    return render(request, 'carrito.html', {'cart_detail': cart_data, 'totales': totales})

def create_product(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            # Resolver vendedor_id del usuario autenticado
            vendedor_id = 1  # fallback
            if request.user.is_authenticated:
                try:
                    vendedor_id = request.user.vendedor_profile.id
                except Exception:
                    pass

            producto_domain = Producto(
                id=None,
                nombre=form.cleaned_data['nombre'],
                categoria_id=form.cleaned_data['categoria'].id,
                subcategoria=form.cleaned_data['subcategoria'],
                marca=form.cleaned_data['marca'],
                es_original=form.cleaned_data['es_original'] == 'True' or form.cleaned_data['es_original'] is True,
                color=form.cleaned_data['color'],
                tamano=form.cleaned_data['tamano'],
                peso=float(form.cleaned_data['peso']),
                talla=form.cleaned_data['talla'],
                es_nuevo=form.cleaned_data['es_nuevo'] == 'True' or form.cleaned_data['es_nuevo'] is True,
                vendedor_id=vendedor_id,
                cantidad_disponible=form.cleaned_data['cantidad_disponible'],
                valor_unitario=float(form.cleaned_data['valor_unitario']),
                caracteristicas=form.cleaned_data['caracteristicas'],
                imagenes=[],
            )
            try:
                # Proxy verifica que el vendedor este ACTIVO antes de guardar
                # Decorator registra la operacion en auditoria de forma transparente
                use_case = get_crear_producto_use_case_con_proxy(
                    vendedor_id=vendedor_id,
                    usuario_id=request.user.id if request.user.is_authenticated else None
                )
                producto_guardado = use_case.execute(producto_domain)
                
                # Guardar imagenes adjuntas
                imagenes = request.FILES.getlist('imagenes_producto')
                for img in imagenes:
                    from core.models import ProductoImagen
                    ProductoImagen.objects.create(producto_id=producto_guardado.id, imagen=img)

                messages.success(request, 'Producto publicado exitosamente.')
                return redirect('vendedor_dashboard')
            except PermissionError as e:
                messages.error(request, str(e))
    else:
        form = ProductoForm()
    return render(request, 'crear_producto.html', {'form': form})

def checkout(request):
    cart_data = request.session.get('cart', {'items': []})
    if not cart_data['items']:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect('catalog')

    if request.method == 'POST':
        metodo_pago_str = request.POST.get('metodo_pago')
        con_domicilio = request.POST.get('con_domicilio') == 'true'
        
        try:
            metodo_pago = MetodoPago(metodo_pago_str)
        except ValueError:
            messages.error(request, "Método de pago no válido.")
            return redirect('view_cart')

        comprador_id = request.user.id if request.user.is_authenticated else 1
        
        # 1. Preparar Carrito y Cálculos
        carrito_items = [
            CarritoItem(
                producto_id=item['producto_id'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario']
            ) for item in cart_data['items']
        ]
        cart = Carrito(comprador_id=comprador_id, items=carrito_items)
        
        # 2. Usar Facade para validación y persistencia inicial
        try:
            from .models import ConfiguracionSistema, Producto as ProductoModel
            config = ConfiguracionSistema.get_config()
            subtotal = 0
            total_comision = 0
            total_iva = 0
            peso_total = 0
            for item in cart.items:
                prod = ProductoModel.objects.get(id=item.producto_id)
                sub_item = item.cantidad * item.precio_unitario
                subtotal += sub_item
                total_comision += sub_item * (prod.categoria.porcentaje_comision / 100)
                peso_total += prod.peso * item.cantidad
                if not prod.categoria.es_iva_incluido:
                    total_iva += sub_item * config.porcentaje_iva
            
            envio = 0
            if con_domicilio:
                envio = config.costo_domicilio_base + (peso_total * config.costo_domicilio_por_kg)
            
            total = subtotal + total_comision + total_iva + envio

            # Crear el pedido en estado PENDIENTE
            pedido_model = Pedido.objects.create(
                comprador_id=comprador_id,
                subtotal=subtotal,
                comision=total_comision,
                envio=envio,
                iva=total_iva,
                total=total,
                metodo_pago=metodo_pago.value,
                estado="PENDIENTE"
            )
            for item in cart.items:
                PedidoItem.objects.create(
                    pedido=pedido_model,
                    producto_id=item.producto_id,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario
                )

            # Guardar en sesión para los views de pago
            request.session['checkout_pedido_id'] = pedido_model.id
            request.session['checkout_total'] = total
            
            # 3. Redirigir según método de pago
            if metodo_pago == MetodoPago.LINEA:
                return redirect('pago_en_linea')
            elif metodo_pago == MetodoPago.TARJETA:
                return redirect('pago_tarjeta')
            else:
                return redirect('pago_consignacion')

        except Exception as e:
            messages.error(request, f"Error iniciando el checkout: {str(e)}")
            return redirect('view_cart')

    return redirect('view_cart')

def bam_dashboard(request):
    # Singleton: siempre la misma instancia de BAMService
    bam = get_bam_service()
    kpis = bam.get_kpis()
    auditorias = Auditoria.objects.all().order_by('-fecha')[:10]
    return render(request, 'bam_dashboard.html', {'kpis': kpis, 'auditorias': auditorias})


def gestionar_suscripcion(request, vendedor_id):
    """Vista del director para gestionar el estado de suscripcion de un vendedor."""
    if request.method == 'POST':
        accion = request.POST.get('accion')  # 'mora', 'reactivar', 'cancelar'
        motivo = request.POST.get('motivo', '')
        # Observer: el use case notifica a todos los observadores registrados
        use_case = get_suscripcion_use_case()
        if accion == 'mora':
            resultado = use_case.marcar_mora(vendedor_id)
        elif accion == 'reactivar':
            resultado = use_case.reactivar(vendedor_id)
        elif accion == 'cancelar':
            resultado = use_case.cancelar(vendedor_id, motivo)
        else:
            resultado = {'success': False, 'message': 'Accion no reconocida.'}

        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
    return redirect('dashboard_director')


# ── Vistas PQRS ───────────────────────────────────────────────────────────────

def crear_pqrs(request):
    """
    Vista para que los usuarios radiquen una solicitud PQRS.
    Usa PQRSFactory (Factory Method) para crear el tipo correcto
    sin exponer la lógica de instanciación a la vista.
    """
    tipos = PQRSFactory.tipos_disponibles()

    if request.method == 'POST':
        tipo = request.POST.get('tipo', '').upper()
        descripcion = request.POST.get('descripcion', '').strip()

        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesion para radicar una PQRS.')
            return redirect('inicio')

        try:
            resultado = RadicarPQRSUseCase().execute(tipo, request.user, descripcion)
            messages.success(request, resultado['message'])
            return redirect('listar_pqrs')
        except (ValueError, Exception) as e:
            messages.error(request, str(e))

    return render(request, 'crear-pqrs.html', {'tipos': tipos})


def listar_pqrs(request):
    """Lista las PQRS del usuario autenticado con su ruta de estados."""
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesion.')
        return redirect('inicio')

    use_case = GestionarPQRSUseCase()
    pqrs_list = use_case.listar(usuario=request.user, solo_activas=False)
    return render(request, 'listar_pqrs.html', {'pqrs_list': pqrs_list})


def detalle_pqrs(request, pqrs_id):
    """Detalle de una PQRS con la traza del Routing Slip."""
    use_case = GestionarPQRSUseCase()
    pqrs = use_case.obtener(pqrs_id)
    if not pqrs:
        messages.error(request, f'PQRS #{pqrs_id} no encontrada.')
        return redirect('listar_pqrs')
    # La ruta_estados contiene el Routing Slip: "RADICADA -> EN_GESTION -> RESPONDIDA"
    ruta = pqrs.ruta_estados.split(' -> ')
    return render(request, 'detalle_pqrs.html', {'pqrs': pqrs, 'ruta': ruta})


def gestion_pqrs(request):
    """Dashboard del gestor: lista y gestiona todas las PQRS."""
    use_case = GestionarPQRSUseCase()

    if request.method == 'POST':
        pqrs_id = request.POST.get('pqrs_id')
        nuevo_estado = request.POST.get('nuevo_estado', '').upper()
        respuesta_texto = request.POST.get('respuesta', '').strip()
        resultado = use_case.avanzar_estado(
            int(pqrs_id), nuevo_estado, request.user, respuesta_texto
        )
        if resultado['success']:
            messages.success(request, resultado['message'])
        else:
            messages.error(request, resultado['message'])
        return redirect('gestion_pqrs')

    todas = use_case.listar(usuario=None, solo_activas=False)
    return render(request, 'gestion_pqrs.html', {
        'pqrs_list': todas,
        'usuario': request.user,
        'estados_siguientes': ['EN_GESTION', 'RESPONDIDA', 'CERRADA'],
    })

def registrar_comprador(request):
    from core.forms import CompradorForm
    from django.contrib.auth.models import User
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    import string
    import random
    
    if request.method == 'POST':
        form = CompradorForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['correo_electronico']
            identificacion = form.cleaned_data['numero_identificacion']
            nombres = form.cleaned_data['nombres']
            
            if User.objects.filter(username=identificacion).exists():
                messages.error(request, 'Ya existe una cuenta con esa identificación.')
            else:
                # Generar contraseña segura aleatoria
                caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
                password = ''.join(random.choice(caracteres) for i in range(12))
                password = 'A1a' + password
                
                user = User.objects.create_user(username=identificacion, email=email, password=password)
                user.first_name = nombres
                user.last_name = form.cleaned_data['apellidos']
                user.save()
                
                comprador = form.save(commit=False)
                comprador.usuario = user
                comprador.save()
                
                # Enviar credenciales (HTML Template)
                try:
                    asunto = 'Bienvenido a Comercial Konrad - Credenciales'
                    context = {
                        'nombres': nombres,
                        'username': identificacion,
                        'password': password
                    }
                    html_content = render_to_string('emails/bienvenida_comprador.html', context)
                    text_content = strip_tags(html_content)
                    
                    msg = EmailMultiAlternatives(
                        asunto,
                        text_content,
                        settings.DEFAULT_FROM_EMAIL,
                        [email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send(fail_silently=False)
                    
                    messages.success(request, 'Registro exitoso. Se enviaron tus credenciales de acceso a tu correo electrónico.')
                    return redirect('login')
                except Exception as e:
                    messages.warning(request, f'Registro exitoso, pero hubo un problema enviando el correo: {e}')
                    return redirect('login')
    else:
        form = CompradorForm()
        
    return render(request, 'registrar_comprador.html', {'form': form})

def detalle_producto(request, producto_id):
    producto = get_object_or_404(ProductoModel, id=producto_id)
    user_es_comprador = False
    if request.user.is_authenticated:
        user_es_comprador = Comprador.objects.filter(usuario=request.user).exists()
    return render(request, 'producto_detalle.html', {
        'producto': producto,
        'user_es_comprador': user_es_comprador,
    })

def agregar_comentario(request, producto_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión.')
        return redirect('login')
    try:
        comprador = Comprador.objects.get(usuario=request.user)
    except Comprador.DoesNotExist:
        messages.error(request, 'Solo los compradores registrados pueden comentar.')
        return redirect('detalle_producto', producto_id=producto_id)

    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()
        es_pregunta = request.POST.get('es_pregunta', 'False') == 'True'
        if texto:
            ComentarioProducto.objects.create(
                producto_id=producto_id,
                comprador=comprador,
                es_pregunta=es_pregunta,
                texto=texto,
            )
            messages.success(request, 'Tu comentario fue enviado.')
    return redirect('detalle_producto', producto_id=producto_id)

def calificar_transaccion(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if request.method == 'POST':
        puntaje = int(request.POST.get('puntaje', 0))
        comentario = request.POST.get('comentario', '').strip()

        if not 1 <= puntaje <= 10:
            messages.error(request, 'La calificación debe estar entre 1 y 10.')
            return redirect('calificar_transaccion', pedido_id=pedido_id)

        try:
            comprador = Comprador.objects.get(usuario=request.user)
        except Comprador.DoesNotExist:
            messages.error(request, 'Solo los compradores registrados pueden calificar.')
            return redirect('catalog')

        vendedor_ids = (
            PedidoItem.objects.filter(pedido=pedido)
            .values_list('producto__vendedor_id', flat=True)
            .distinct()
        )
        for vendedor_id in vendedor_ids:
            vendedor = VendedorModel.objects.get(id=vendedor_id)
            CalificacionTransaccion.objects.get_or_create(
                pedido=pedido,
                defaults={
                    'comprador': comprador,
                    'vendedor': vendedor,
                    'puntaje': puntaje,
                    'comentario': comentario,
                }
            )
            # Recalcular promedio y contador de malas calificaciones
            todas = CalificacionTransaccion.objects.filter(vendedor=vendedor)
            promedio = todas.aggregate(Avg('puntaje'))['puntaje__avg'] or 0
            bajas = todas.filter(puntaje__lt=3).count()
            vendedor.calificacion_promedio = promedio
            vendedor.numero_calificaciones_bajas = bajas
            vendedor.save()

            # Si el promedio baja de 5 o tiene 10 calificaciones < 3, se cancela
            if (promedio < 5 and todas.count() >= 1) or bajas >= 10:
                vendedor.estado = 'CANCELADA'
                vendedor.save()
                # Notificar al vendedor
                try:
                    send_mail(
                        'Suscripción Cancelada - Comercial Konrad',
                        f'Lamentamos informarte que tu suscripción ha sido cancelada debido a tu baja calificación ({promedio:.1f}) o por acumular {bajas} calificaciones negativas.',
                        settings.DEFAULT_FROM_EMAIL,
                        [vendedor.solicitud.correo_electronico],
                        fail_silently=True,
                    )
                except: pass

        # Punto 3: Persistencia del comentario en el detalle del producto
        for item in pedido.items.all():
            ComentarioProducto.objects.create(
                producto=item.producto,
                comprador=comprador,
                texto=f"[Calificación {puntaje}/10]: {comentario}",
                es_pregunta=False
            )

        messages.success(request, '🎉 ¡Muchas gracias por tu calificación! Tu opinión es muy importante para nosotros.')
        return redirect('inicio')

    return render(request, 'calificar_compra.html', {'pedido': pedido})


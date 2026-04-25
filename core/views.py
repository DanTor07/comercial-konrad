from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import os
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
from .models import SolicitudVendedor as SolicitudVendedorModel, Auditoria, PQRS as PQRSModel, Suscripcion, Producto as ProductoModel

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
    plan = request.session.get('suscripcion_plan', 'MENSUAL')
    precios = {'MENSUAL': 50000, 'SEMESTRAL': 250000, 'ANUAL': 450000}
    
    if request.method == 'POST':
        # Generar comprobante de aprobación bancaria
        num_aprobacion = str(uuid.uuid4()).split('-')[0].upper()
        _activar_suscripcion(request.user.vendedor_profile, plan)
        messages.success(request, f'Pago aprobado. Nro de aprobación bancaria: {num_aprobacion}')
        return redirect('vendedor_dashboard')
        
    return render(request, 'pagos/en_linea.html', {'plan': plan, 'precio': precios[plan]})

@login_required(login_url='login')
def pago_tarjeta(request):
    plan = request.session.get('suscripcion_plan', 'MENSUAL')
    precios = {'MENSUAL': 50000, 'SEMESTRAL': 250000, 'ANUAL': 450000}
    
    if request.method == 'POST':
        # Procesar cargo a la tarjeta de crédito
        _activar_suscripcion(request.user.vendedor_profile, plan)
        messages.success(request, 'Pago con Tarjeta de Crédito procesado exitosamente.')
        return redirect('vendedor_dashboard')
        
    return render(request, 'pagos/tarjeta.html', {'plan': plan, 'precio': precios[plan]})

@login_required(login_url='login')
def pago_consignacion(request):
    plan = request.session.get('suscripcion_plan', 'MENSUAL')
    precios = {'MENSUAL': 50000, 'SEMESTRAL': 250000, 'ANUAL': 450000}
    vendedor = request.user.vendedor_profile
    
    if request.method == 'POST':
        # Procesamiento batch de recaudo bancario (Lectura de archivo plano)
        file_path = os.path.join(settings.BASE_DIR, 'banco_consignaciones.txt')
        
        # Escribir registro temporal para procesar el lote actual
        with open(file_path, 'w') as f:
            f.write(f"{vendedor.solicitud.numero_identificacion},PAGADO\n")
            
        # Ejecutar lectura de conciliación
        with open(file_path, 'r') as f:
            lineas = f.readlines()
            for linea in lineas:
                cedula, estado = linea.strip().split(',')
                if cedula == vendedor.solicitud.numero_identificacion and estado == 'PAGADO':
                    _activar_suscripcion(vendedor, plan)
                    messages.success(request, 'El archivo de recaudo bancario ha sido procesado exitosamente. Se ha confirmado tu pago y tu suscripción está activa.')
                    return redirect('vendedor_dashboard')
                    
        messages.error(request, 'No se encontró el pago en el archivo bancario.')
        return redirect('vendedor_dashboard')
        
    return render(request, 'pagos/consignacion.html', {'plan': plan, 'precio': precios[plan], 'vendedor': vendedor})

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
    categorias = get_listar_categorias_use_case().execute()
    criteria = {'q': request.GET.get('q'), 'categoria': request.GET.get('categoria')}
    productos = get_buscar_productos_use_case().execute(criteria)
    return render(request, 'catalogo.html', {'categorias': categorias, 'productos': productos})

def add_to_cart(request, producto_id):
    cart_data = request.session.get('cart', {'items': []})
    cart = Carrito(comprador_id=0, items=[CarritoItem(**item) for item in cart_data['items']])
    try:
        get_gestionar_carrito_use_case().agregar_producto(cart, producto_id, 1)
        request.session['cart'] = {'items': [vars(item) for item in cart.items]}
        messages.success(request, 'Producto añadido.')
    except Exception as e:
        messages.error(request, str(e))
    return redirect('catalog')

def view_cart(request):
    cart_data = request.session.get('cart', {'items': []})
    return render(request, 'carrito.html', {'cart': cart_data})

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
        metodo_pago = MetodoPago(metodo_pago_str)
        comprador_id = request.user.id if request.user.is_authenticated else 1
        cart = Carrito(
            comprador_id=comprador_id,
            items=[CarritoItem(**item) for item in cart_data['items']]
        )
        try:
            # Facade coordina: validación de stock, pago (Strategy),
            # persistencia atómica en BD y actualización de stock (con Decorator de auditoría)
            facade = get_checkout_facade(usuario_id=comprador_id)
            resultado = facade.procesar(cart, metodo_pago, comprador_id)

            if resultado['success']:
                request.session['cart'] = {'items': []}
                return render(request, 'checkout_success.html', {'resultado': resultado})
            else:
                messages.error(request, resultado['message'])
        except Exception as e:
            messages.error(request, f"Error en el checkout: {str(e)}")

    return render(request, 'checkout.html', {'cart': cart_data})

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

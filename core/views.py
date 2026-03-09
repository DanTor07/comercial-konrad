from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SolicitudVendedorForm, ProductoForm
from .infrastructure.dependencies import (
    get_registrar_solicitud_use_case, 
    get_procesar_decision_use_case,
    get_listar_categorias_use_case,
    get_buscar_productos_use_case,
    get_gestionar_carrito_use_case,
    get_crear_producto_use_case,
    get_procesar_checkout_use_case
)
from .domain.entities.vendedor import SolicitudVendedor, SolicitudEstado
from .domain.entities.venta import Carrito, CarritoItem, MetodoPago
from .domain.entities.producto import Producto
from .infrastructure.services.monitoring import BAMService

def home(request):
    return render(request, 'inicio.html')

def registrar_vendedor(request):
    if request.method == 'POST':
        form = SolicitudVendedorForm(request.POST)
        if form.is_valid():
            solicitud = SolicitudVendedor(
                id=None, nombres=form.cleaned_data['nombres'], apellidos=form.cleaned_data['apellidos'],
                numero_identificacion=form.cleaned_data['numero_identificacion'], correo_electronico=form.cleaned_data['correo_electronico'],
                pais=form.cleaned_data['pais'], ciudad=form.cleaned_data['ciudad'], telefono=form.cleaned_data['telefono'], documentos=[]
            )
            get_registrar_solicitud_use_case().execute(solicitud)
            messages.success(request, 'Solicitud registrada.')
            return redirect('inicio')
    else:
        form = SolicitudVendedorForm()
    return render(request, 'registrar_vendedor.html', {'form': form})

def dashboard_director(request):
    from .models import SolicitudVendedor as SolicitudModel
    solicitudes = SolicitudModel.objects.filter(estado='PENDIENTE')
    return render(request, 'director/dashboard.html', {'solicitudes': solicitudes})

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
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto_domain = Producto(
                id=None, nombre=form.cleaned_data['nombre'], categoria_id=form.cleaned_data['categoria'].id,
                subcategoria=form.cleaned_data['subcategoria'], marca=form.cleaned_data['marca'],
                es_original=form.cleaned_data['es_original'], color=form.cleaned_data['color'],
                tamano=form.cleaned_data['tamano'], peso=float(form.cleaned_data['peso']),
                talla=form.cleaned_data['talla'], es_nuevo=form.cleaned_data['es_nuevo'],
                vendedor_id=1, cantidad_disponible=form.cleaned_data['cantidad_disponible'],
                valor_unitario=float(form.cleaned_data['valor_unitario']), caracteristicas=form.cleaned_data['caracteristicas'],
                imagenes=[], calificacion=0.0
            )
            get_crear_producto_use_case().execute(producto_domain)
            messages.success(request, 'Producto publicado.')
            return redirect('catalog')
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
        cart = Carrito(comprador_id=1, items=[CarritoItem(**item) for item in cart_data['items']])
        try:
            pedido = get_procesar_checkout_use_case().execute(cart, metodo_pago)
            if pedido.estado == "PAGADO":
                request.session['cart'] = {'items': []}
                return render(request, 'checkout_success.html', {'pedido': pedido})
            else:
                messages.error(request, "El pago no pudo ser procesado.")
        except Exception as e:
            messages.error(request, f"Error en el checkout: {str(e)}")
    return render(request, 'checkout.html', {'cart': cart_data})

def bam_dashboard(request):
    kpis = BAMService.get_kpis()
    from .models import Auditoria
    auditorias = Auditoria.objects.all().order_by('-fecha')[:10]
    return render(request, 'bam_dashboard.html', {'kpis': kpis, 'auditorias': auditorias})

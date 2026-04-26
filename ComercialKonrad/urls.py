from django.contrib import admin
from django.urls import path
from core.views import (
    home, registrar_vendedor, dashboard_director,
    procesar_solicitud, detalle_solicitud, catalog, add_to_cart,
    add_to_cart_qty_inc, add_to_cart_qty_dec, remove_from_cart,
    view_cart, create_product,
    checkout, bam_dashboard,
    gestionar_suscripcion, custom_login, custom_logout, vendedor_dashboard,
    crear_pqrs, listar_pqrs, detalle_pqrs, gestion_pqrs,
    iniciar_pago_suscripcion, pago_en_linea, pago_tarjeta, pago_consignacion,
    consultar_estado, registrar_comprador, detalle_producto,
    agregar_comentario, calificar_transaccion,
)
from core.interfaces.api.api_views import get_simulated_sales, get_simulated_sellers
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='inicio'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('vendedor/dashboard/', vendedor_dashboard, name='vendedor_dashboard'),
    path('vendedor/pagar/', iniciar_pago_suscripcion, name='iniciar_pago_suscripcion'),
    path('vendedor/pagar/en-linea/', pago_en_linea, name='pago_en_linea'),
    path('vendedor/pagar/tarjeta/', pago_tarjeta, name='pago_tarjeta'),
    path('vendedor/pagar/consignacion/', pago_consignacion, name='pago_consignacion'),
    path('catalog/', catalog, name='catalog'),
    path('catalog/new/', create_product, name='create_product'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/add/<int:producto_id>/', add_to_cart, name='add_to_cart'),
    path('cart/qty/inc/<int:producto_id>/', add_to_cart_qty_inc, name='add_to_cart_qty_inc'),
    path('cart/qty/dec/<int:producto_id>/', add_to_cart_qty_dec, name='add_to_cart_qty_dec'),
    path('cart/remove/<int:producto_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('checkout/<int:pedido_id>/calificar/', calificar_transaccion, name='calificar_transaccion'),
    path('bam/', bam_dashboard, name='bam_dashboard'),
    path('registrar/', registrar_comprador, name='registrar_comprador'),
    path('registrar-vendedor/', registrar_vendedor, name='registrar_vendedor'),
    path('consultar-estado/', consultar_estado, name='consultar_estado'),
    path('director/', dashboard_director, name='dashboard_director'),
    path('director/solicitud/<int:solicitud_id>/', procesar_solicitud, name='procesar_solicitud'),
    path('director/detalle/<int:solicitud_id>/', detalle_solicitud, name='detalle_solicitud'),
    path('director/suscripcion/<int:vendedor_id>/', gestionar_suscripcion, name='gestionar_suscripcion'),
    path('catalog/producto/<int:producto_id>/', detalle_producto, name='detalle_producto'),
    path('catalog/producto/<int:producto_id>/comentar/', agregar_comentario, name='agregar_comentario'),
    # API REST (Externa)
    path('api/ventas/', get_simulated_sales, name='api_ventas'),
    path('api/vendedores/', get_simulated_sellers, name='api_vendedores'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.urls import path
from core.views import (
    home, registrar_vendedor, dashboard_director,
    procesar_solicitud, catalog, add_to_cart,
    view_cart, create_product, checkout, bam_dashboard,
    gestionar_suscripcion
)
from core.interfaces.api.api_views import get_simulated_sales, get_simulated_sellers
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='inicio'),
    path('catalog/', catalog, name='catalog'),
    path('catalog/new/', create_product, name='create_product'),
    path('cart/', view_cart, name='view_cart'),
    path('cart/add/<int:producto_id>/', add_to_cart, name='add_to_cart'),
    path('checkout/', checkout, name='checkout'),
    path('bam/', bam_dashboard, name='bam_dashboard'),
    path('registrar-vendedor/', registrar_vendedor, name='registrar_vendedor'),
    path('director/', dashboard_director, name='dashboard_director'),
    path('director/procesar/<int:solicitud_id>/', procesar_solicitud, name='procesar_solicitud'),
    path('director/suscripcion/<int:vendedor_id>/', gestionar_suscripcion, name='gestionar_suscripcion'),
    # API REST (Externa)
    path('api/ventas/', get_simulated_sales, name='api_ventas'),
    path('api/vendedores/', get_simulated_sellers, name='api_vendedores'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
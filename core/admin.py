from django.contrib import admin
from .models import Categoria, SolicitudVendedor, DocumentoAdjunto, Vendedor, Suscripcion, Producto, ProductoImagen, Auditoria, LogError

admin.site.register(Categoria)
admin.site.register(SolicitudVendedor)
admin.site.register(DocumentoAdjunto)
admin.site.register(Vendedor)
admin.site.register(Suscripcion)
admin.site.register(Producto)
admin.site.register(ProductoImagen)
admin.site.register(Auditoria)
admin.site.register(LogError)
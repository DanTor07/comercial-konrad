from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje_comision = models.FloatField(help_text="Porcentaje de comisión (ej. 0.1 para 10%)")
    porcentaje_iva = models.FloatField(default=0.19, help_text="Porcentaje de IVA (ej. 0.19)")
    domicilio_base = models.FloatField(default=10000, help_text="Costo base de domicilio para esta categoría")
    es_iva_incluido = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class SolicitudVendedor(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('RECHAZADA', 'Rechazada'),
        ('DEVUELTA', 'Devuelta'),
        ('APROBADA', 'Aprobada'),
    ]
    TIPO_PERSONA_CHOICES = [
        ('NATURAL', 'Persona Natural'),
        ('JURIDICA', 'Persona Jurídica'),
    ]
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA_CHOICES, default='NATURAL')
    numero_identificacion = models.CharField(max_length=20, unique=True)
    correo_electronico = models.EmailField()
    pais = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    comentarios_director = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    score_datacredito = models.CharField(max_length=20, blank=True, null=True)
    score_cifin = models.CharField(max_length=20, blank=True, null=True)
    tiene_antecedentes = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.numero_identificacion}"

class DocumentoAdjunto(models.Model) :
    solicitud = models.ForeignKey(SolicitudVendedor, related_name='documentos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=50)
    archivo = models.FileField(upload_to='vendedores/documentos/')

class Vendedor(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('EN MORA', 'En Mora'),
        ('CANCELADA', 'Cancelada'),
    ]
    solicitud = models.OneToOneField(SolicitudVendedor, on_delete=models.PROTECT)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendedor_profile')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVA')
    calificacion_promedio = models.FloatField(default=0.0)
    numero_calificaciones_bajas = models.IntegerField(default=0)

    def __str__(self):
        return self.solicitud.numero_identificacion

class Comprador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='comprador_profile')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    numero_identificacion = models.CharField(max_length=20, unique=True)
    correo_electronico = models.EmailField()
    pais = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class Suscripcion(models.Model):
    TIPO_CHOICES = [
        ('MENSUAL', 'Mensual'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
    ]
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    tipo_facturacion = models.CharField(max_length=10, choices=TIPO_CHOICES)
    esta_activa = models.BooleanField(default=True)

class Producto(models.Model):
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    subcategoria = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    es_original = models.BooleanField(default=True)
    color = models.CharField(max_length=50)
    tamano = models.CharField(max_length=50)
    peso = models.FloatField()
    talla = models.CharField(max_length=20)
    es_nuevo = models.BooleanField(default=True)
    cantidad_disponible = models.IntegerField()
    valor_unitario = models.FloatField()
    caracteristicas = models.TextField()

    def __str__(self):
        return self.nombre

class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/')

class ComentarioProducto(models.Model):
    producto = models.ForeignKey(Producto, related_name='comentarios', on_delete=models.CASCADE)
    comprador = models.ForeignKey(Comprador, on_delete=models.CASCADE)
    es_pregunta = models.BooleanField(default=False)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    respuesta_vendedor = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Comentario de {self.comprador.nombres} en {self.producto.nombre}"

class Auditoria(models.Model):
    accion = models.CharField(max_length=100)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    detalles = models.TextField()

class LogError(models.Model):
    mensaje = models.TextField()
    stack_trace = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

class Pedido(models.Model):
    comprador = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.FloatField(default=0.0)
    comision = models.FloatField(default=0.0)
    envio = models.FloatField(default=0.0)
    iva = models.FloatField(default=0.0)
    total = models.FloatField()
    metodo_pago = models.CharField(max_length=20)
    estado = models.CharField(max_length=20, default='PENDIENTE')

    def __str__(self):
        return f"Pedido {self.id} - {self.comprador.username}"

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.FloatField()

class CalificacionTransaccion(models.Model):
    pedido = models.OneToOneField(Pedido, related_name='calificacion', on_delete=models.CASCADE)
    comprador = models.ForeignKey(Comprador, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE)
    puntaje = models.IntegerField(choices=[(i, str(i)) for i in range(1, 11)]) # 1 to 10
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

class ConfiguracionSistema(models.Model):
    # Singleton para configuraciones globales
    porcentaje_iva = models.FloatField(default=0.19)
    costo_domicilio_base = models.FloatField(default=10000.0)
    costo_domicilio_por_kg = models.FloatField(default=1000.0)

    @classmethod
    def get_config(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj




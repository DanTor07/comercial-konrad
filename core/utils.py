import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import hashlib
import datetime


def generar_contrasena_segura(longitud=8):
    if longitud < 4:
        raise ValueError("La longitud debe ser al menos 4 para cumplir los requisitos mínimos.")

    mayuscula = random.choice(string.ascii_uppercase)
    minuscula = random.choice(string.ascii_lowercase)
    numero = random.choice(string.digits)
    especial = random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")

    obligatorios = [mayuscula, minuscula, numero, especial]

    if longitud > 4:
        restantes = random.choices(string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?", k=longitud - 4)
        obligatorios += restantes

    random.shuffle(obligatorios)
    return ''.join(obligatorios)

def enviar_correo_bienvenida(email, nombre, numero_id, contrasena, numero_radicado, tipo_radicado, codigo_verificacion):
    asunto = 'Bienvenido al sistema de PQRS - Verifica tu cuenta'
    mensaje = f'''
Hola {nombre},

Tu cuenta ha sido creada exitosamente en nuestra plataforma de PQRS.

Aquí están tus datos de acceso:

👤 Usuario: {numero_id}
🔐 Contraseña temporal: {contrasena}

Detalles de tu PQRS:

📄 Número de radicado: {numero_radicado}
📂 Tipo de radicado: {tipo_radicado}

Para activar tu cuenta y confirmar que no eres un bot, por favor haz clic en el siguiente enlace de verificación:

🔗 http://localhost:8000/verificar/{codigo_verificacion}

Una vez verificado, podrás iniciar sesión en nuestra plataforma y gestionar tus solicitudes. Te recomendamos cambiar la contraseña tras el primer acceso.

Gracias por confiar en nosotros.

Si no te registraste, por favor ignora este mensaje.

Atentamente,
Equipo de PQRS
    '''
    remitente = settings.EMAIL_HOST_USER
    send_mail(asunto, mensaje, remitente, [email])


def generar_token_personalizado(cliente):
    now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    data = f"{cliente.pk}{cliente.correo_electronico}{now}"
    return hashlib.sha256(data.encode()).hexdigest()


def enviar_correo_recuperacion(cliente, request):
    token = generar_token_personalizado(cliente)
    cliente.token_recuperacion = token
    cliente.save()

    url = request.build_absolute_uri(reverse('restablecer_contrasena', args=[token]))

    asunto = 'Recuperación de contraseña'
    mensaje = f"""Hola {cliente.nombre_completo},

Haz clic en el siguiente enlace para restablecer tu contraseña:

{url}

Si tú no solicitaste este cambio, puedes ignorar este mensaje.
"""

    send_mail(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        [cliente.correo_electronico],
        fail_silently=False,
    )

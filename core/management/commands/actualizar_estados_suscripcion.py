from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Vendedor, Suscripcion
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Actualiza el estado de los vendedores (EN MORA / CANCELADA) según el vencimiento de su suscripción'

    def handle(self, *args, **options):
        hoy = timezone.now()
        un_mes_atras = hoy - timedelta(days=30)
        
        vendedores = Vendedor.objects.filter(estado__in=['ACTIVA', 'EN MORA'])
        
        actualizados_mora = 0
        actualizados_cancelada = 0

        for vendedor in vendedores:
            # Cancelación por baja calificación
            if vendedor.numero_calificaciones_bajas >= 10 or (vendedor.calificacion_promedio > 0 and vendedor.calificacion_promedio < 5):
                vendedor.estado = 'CANCELADA'
                vendedor.save()
                actualizados_cancelada += 1
                self.enviar_correo_cancelacion_por_calificacion(vendedor)
                self.stdout.write(self.style.ERROR(f"Vendedor {vendedor.solicitud.numero_identificacion} pasado a CANCELADA por malas calificaciones."))
                continue

            # Obtener la suscripción más reciente para validación de mora
            ultima_suscripcion = Suscripcion.objects.filter(vendedor=vendedor).order_by('-fecha_fin').first()
            
            if not ultima_suscripcion:
                continue

            # Si el vendedor está activo y ya pasó la fecha de fin (al menos un día)
            if vendedor.estado == 'ACTIVA' and ultima_suscripcion.fecha_fin < hoy:
                vendedor.estado = 'EN MORA'
                ultima_suscripcion.esta_activa = False
                ultima_suscripcion.save()
                vendedor.save()
                actualizados_mora += 1
                
                self.enviar_correo_mora(vendedor)
                self.stdout.write(self.style.WARNING(f"Vendedor {vendedor.solicitud.numero_identificacion} pasado a EN MORA."))

            elif vendedor.estado == 'EN MORA' and ultima_suscripcion.fecha_fin < un_mes_atras:
                vendedor.estado = 'CANCELADA'
                vendedor.save()
                actualizados_cancelada += 1
                
                self.enviar_correo_cancelacion(vendedor)
                self.stdout.write(self.style.ERROR(f"Vendedor {vendedor.solicitud.numero_identificacion} pasado a CANCELADA."))

        self.stdout.write(self.style.SUCCESS(f'Proceso finalizado. {actualizados_mora} pasados a EN MORA, {actualizados_cancelada} pasados a CANCELADA.'))

    def enviar_correo_mora(self, vendedor):
        asunto = '⚠️ Acción Requerida: Tu suscripción está EN MORA'
        
        html_mensaje = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #B45309; text-align: center;">Aviso Importante</h2>
                <p style="font-size: 16px; color: #333333;">Hola <strong>{vendedor.solicitud.nombres} {vendedor.solicitud.apellidos}</strong>,</p>
                <p style="font-size: 16px; color: #333333;">
                    Te informamos que tu suscripción en Comercial Konrad ha finalizado. Tu cuenta ha pasado a estado <strong style="color: #DC2626;">EN MORA</strong>.
                </p>
                <p style="font-size: 16px; color: #333333;">
                    Para seguir vendiendo tus productos y evitar que tu cuenta sea cancelada permanentemente dentro de 30 días, por favor renueva tu suscripción.
                </p>
                <div style="text-align: center; margin-top: 30px; margin-bottom: 30px;">
                    <a href="http://127.0.0.1:8000/login/" style="background-color: #F59E0B; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">
                        Renovar Suscripción Ahora
                    </a>
                </div>
                <hr style="border: none; border-top: 1px solid #eeeeee;">
                <p style="font-size: 12px; color: #999999; text-align: center;">
                    Este es un correo automático, por favor no respondas a este mensaje.<br>
                    © 2026 Comercial Konrad.
                </p>
            </div>
        </body>
        </html>
        """

        mensaje_plano = (
            f"Hola {vendedor.solicitud.nombres} {vendedor.solicitud.apellidos},\n\n"
            f"Tu suscripción ha finalizado y estás EN MORA. Por favor, renueva tu suscripción ingresando al portal.\n"
        )
        try:
            send_mail(
                asunto,
                mensaje_plano,
                settings.DEFAULT_FROM_EMAIL,
                [vendedor.solicitud.correo_electronico],
                html_message=html_mensaje,
                fail_silently=True,
            )
        except Exception as e:
            self.stderr.write(f"Error enviando correo a {vendedor.solicitud.correo_electronico}: {e}")

    def enviar_correo_cancelacion(self, vendedor):
        asunto = '❌ Tu cuenta ha sido CANCELADA definitivamente'
        
        html_mensaje = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; border-top: 5px solid #DC2626; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #DC2626; text-align: center;">Cuenta Cancelada</h2>
                <p style="font-size: 16px; color: #333333;">Hola <strong>{vendedor.solicitud.nombres} {vendedor.solicitud.apellidos}</strong>,</p>
                <p style="font-size: 16px; color: #333333;">
                    Te informamos que, al haber pasado más de un mes desde el vencimiento de tu suscripción sin registrar un nuevo pago, 
                    tu cuenta en Comercial Konrad ha sido <strong>CANCELADA definitivamente</strong>.
                </p>
                <p style="font-size: 16px; color: #333333;">
                    A partir de este momento, tus productos han sido retirados del catálogo público y no podrás acceder a tu portal de ventas.
                </p>
                <p style="font-size: 16px; color: #333333;">
                    Lamentamos verte partir. Si deseas volver a vender con nosotros en el futuro, deberás iniciar un nuevo proceso de registro.
                </p>
                <hr style="border: none; border-top: 1px solid #eeeeee; margin-top: 30px;">
                <p style="font-size: 12px; color: #999999; text-align: center;">
                    Este es un correo automático, por favor no respondas a este mensaje.<br>
                    © 2026 Comercial Konrad.
                </p>
            </div>
        </body>
        </html>
        """

        mensaje_plano = (
            f"Hola {vendedor.solicitud.nombres},\n\n"
            f"Tu cuenta ha sido CANCELADA tras superar el periodo de mora sin pago.\n"
        )
        try:
            send_mail(
                asunto,
                mensaje_plano,
                settings.DEFAULT_FROM_EMAIL,
                [vendedor.solicitud.correo_electronico],
                html_message=html_mensaje,
                fail_silently=True,
            )
        except Exception as e:
            self.stderr.write(f"Error enviando correo a {vendedor.solicitud.correo_electronico}: {e}")

    def enviar_correo_cancelacion_por_calificacion(self, vendedor):
        asunto = '🚫 Tu cuenta ha sido CANCELADA por bajo rendimiento'
        
        html_mensaje = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; border-top: 5px solid #DC2626; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #DC2626; text-align: center;">Cuenta Cancelada por Calificaciones</h2>
                <p style="font-size: 16px; color: #333333;">Hola <strong>{vendedor.solicitud.nombres} {vendedor.solicitud.apellidos}</strong>,</p>
                <p style="font-size: 16px; color: #333333;">
                    Te informamos que debido a que tu cuenta ha acumulado <strong>10 calificaciones por debajo de 3</strong> o tu <strong>promedio ha bajado de 5</strong>, 
                    tu cuenta de vendedor en Comercial Konrad ha sido <strong>CANCELADA definitivamente</strong>.
                </p>
                <p style="font-size: 16px; color: #333333;">
                    Para Comercial Konrad es indispensable mantener altos estándares de calidad y servicio para nuestros clientes.
                    A partir de este momento, tus productos han sido retirados del catálogo público y no podrás acceder a tu portal de ventas.
                </p>
                <hr style="border: none; border-top: 1px solid #eeeeee; margin-top: 30px;">
                <p style="font-size: 12px; color: #999999; text-align: center;">
                    Este es un correo automático, por favor no respondas a este mensaje.<br>
                    © 2026 Comercial Konrad.
                </p>
            </div>
        </body>
        </html>
        """

        mensaje_plano = (
            f"Hola {vendedor.solicitud.nombres},\n\n"
            f"Tu cuenta ha sido CANCELADA debido a bajo rendimiento en tus calificaciones.\n"
        )
        try:
            send_mail(
                asunto,
                mensaje_plano,
                settings.DEFAULT_FROM_EMAIL,
                [vendedor.solicitud.correo_electronico],
                html_message=html_mensaje,
                fail_silently=True,
            )
        except Exception as e:
            self.stderr.write(f"Error enviando correo a {vendedor.solicitud.correo_electronico}: {e}")

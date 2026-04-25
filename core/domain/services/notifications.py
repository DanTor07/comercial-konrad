import logging
from abc import ABC, abstractmethod
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger('audit')


# ── Patrón Observer — Base ────────────────────────────────────────────────────

class Observer(ABC):
    """Interfaz abstracta que todos los observadores deben implementar."""

    @abstractmethod
    def update(self, event_type: str, data: dict):
        pass


class Subject:
    """
    Sujeto genérico: mantiene lista de observadores y les notifica eventos.
    Usado por el sistema de checkout para notificar PEDIDO_PAGADO.
    """

    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    def notify(self, event_type: str, data: dict):
        for observer in self._observers:
            observer.update(event_type, data)


class EmailNotificationObserver(Observer):
    """Observer de checkout: simula envío de email por venta."""

    def update(self, event_type: str, data: dict):
        logger.info(f"[EMAIL] Evento={event_type} | {data.get('message', str(data))}")
        print(f"Email enviado para evento {event_type}: {data.get('message', '')}")


class DashboardUpdateObserver(Observer):
    """Observer de checkout: actualiza KPIs en el BAM Dashboard."""

    def update(self, event_type: str, data: dict):
        logger.info(f"[BAM] KPI actualizado. Evento={event_type} | Total={data.get('total', 0)}")
        print(f"KPI actualizado en BAM para evento {event_type}")


# ── Patrón Observer — Sistema de Suscripciones ───────────────────────────────

class SuscripcionObserver(ABC):
    """
    Patrón: Observer — Interfaz específica para eventos del ciclo de vida
    de la suscripción de un vendedor.
    Distintos consumidores reaccionan de forma independiente al mismo evento.
    """

    @abstractmethod
    def on_suscripcion_event(self, event_type: str, vendedor_id: int, data: dict):
        """
        Args:
            event_type: 'MORA', 'REACTIVADA', 'CANCELADA'
            vendedor_id: ID del vendedor afectado
            data: contexto adicional del evento
        """
        pass


class SuscripcionEmailObserver(SuscripcionObserver):
    """
    Observer 1: Notifica al vendedor por email cuando cambia el estado
    de su suscripción (mora, reactivación, cancelación).
    """

    def on_suscripcion_event(self, event_type: str, vendedor_id: int, data: dict):
        mensajes = {
            'MORA': "Tu suscripcion en Comercial Konrad esta en MORA. Regulariza tu pago para seguir vendiendo.",
            'REACTIVADA': "Tu suscripcion ha sido reactivada. Bienvenido de nuevo!",
            'CANCELADA': "Tu suscripcion ha sido CANCELADA por mora acumulada.",
        }
        mensaje = mensajes.get(event_type, f"Cambio en tu suscripcion: {event_type}")
        logger.info(f"[EMAIL-SUSCRIPCION] Vendedor={vendedor_id} | {event_type} | {mensaje}")
        # En produccion: send_mail(subject, mensaje, from_email, [vendedor.email])
        print(f"[Suscripcion] Vendedor #{vendedor_id} — {mensaje}")


class SuscripcionBAMObserver(SuscripcionObserver):
    """
    Observer 2: Registra el cambio de estado en el log de auditoria
    para que sea visible en el BAM Dashboard.
    """

    def on_suscripcion_event(self, event_type: str, vendedor_id: int, data: dict):
        from ...infrastructure.services.monitoring import AuditService
        detalle = f"Suscripcion Vendedor #{vendedor_id} -> {event_type} | {data}"
        logger.info(f"[BAM-SUSCRIPCION] {detalle}")
        try:
            AuditService.log_action(None, f"SUSCRIPCION_{event_type}", detalle)
        except Exception as e:
            logger.error(f"Error registrando evento de suscripcion en BAM: {e}")


class SuscripcionBlockerObserver(SuscripcionObserver):
    """
    Observer 3: Bloquea o desbloquea al vendedor en BD segun el evento.
    - MORA / CANCELADA => estado EN MORA o CANCELADA
    - REACTIVADA       => estado ACTIVA
    """

    def on_suscripcion_event(self, event_type: str, vendedor_id: int, data: dict):
        from ...models import Vendedor as VendedorModel
        estado_map = {
            'MORA':       'EN MORA',
            'CANCELADA':  'CANCELADA',
            'REACTIVADA': 'ACTIVA',
        }
        nuevo_estado = estado_map.get(event_type)
        if nuevo_estado:
            VendedorModel.objects.filter(id=vendedor_id).update(estado=nuevo_estado)
            logger.info(
                f"[BLOCKER] Vendedor #{vendedor_id} -> estado actualizado a '{nuevo_estado}'"
            )


class SuscripcionSubject:
    """
    Patrón: Observer — Sujeto del sistema de suscripciones.
    Gestiona los observadores y publica eventos del ciclo de vida.

    Uso:
        subject = SuscripcionSubject()
        subject.attach(SuscripcionEmailObserver())
        subject.attach(SuscripcionBAMObserver())
        subject.attach(SuscripcionBlockerObserver())
        subject.publicar_mora(vendedor_id=5, dias_mora=10)
    """

    def __init__(self):
        self._observers: list = []

    def attach(self, observer: SuscripcionObserver):
        self._observers.append(observer)

    def detach(self, observer: SuscripcionObserver):
        self._observers.remove(observer)

    def _publicar(self, event_type: str, vendedor_id: int, data: dict):
        """Notifica a todos los observadores registrados."""
        for obs in self._observers:
            obs.on_suscripcion_event(event_type, vendedor_id, data)

    def publicar_mora(self, vendedor_id: int, dias_mora: int = 0):
        """Publica el evento de mora al vendedor."""
        self._publicar('MORA', vendedor_id, {'dias_mora': dias_mora})

    def publicar_reactivacion(self, vendedor_id: int):
        """Publica el evento de reactivacion de suscripcion."""
        self._publicar('REACTIVADA', vendedor_id, {})

    def publicar_cancelacion(self, vendedor_id: int, motivo: str = ""):
        """Publica el evento de cancelacion definitiva."""
        self._publicar('CANCELADA', vendedor_id, {'motivo': motivo})


# ── Patrón Observer — Sistema de Decisiones del Director ─────────────────────

class DecisionObserver(ABC):
    @abstractmethod
    def on_decision(self, solicitud, decision: str, comentarios: str):
        pass


class DecisionEmailObserver(DecisionObserver):
    """
    Envía un correo HTML al vendedor cuando el director toma una decisión
    sobre su solicitud de registro.
    """
    def on_decision(self, solicitud, decision: str, comentarios: str, extra_data: dict = None):
        extra_data = extra_data or {}
        asunto = f"Comercial Konrad - Actualización de tu solicitud de vendedor"
        
        context = {
            'solicitud': solicitud,
            'decision': decision,
            'comentarios': comentarios,
            'username': extra_data.get('username'),
            'password': extra_data.get('password'),
        }

        # Renderizar la plantilla HTML
        html_content = render_to_string('emails/decision_solicitud.html', context)
        # Generar una versión en texto plano (fallback)
        text_content = strip_tags(html_content)

        try:
            msg = EmailMultiAlternatives(
                asunto,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [solicitud.correo_electronico]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            logger.info(f"[EMAIL-DECISION] Enviado a {solicitud.correo_electronico} | Decision: {decision}")
        except Exception as e:
            logger.error(f"[EMAIL-DECISION] Error enviando correo a {solicitud.correo_electronico}: {e}")


class SolicitudDecisionSubject:
    def __init__(self):
        self._observers: list = []

    def attach(self, observer: DecisionObserver):
        self._observers.append(observer)

    def notify_decision(self, solicitud, decision: str, comentarios: str, extra_data: dict = None):
        for obs in self._observers:
            obs.on_decision(solicitud, decision, comentarios, extra_data)


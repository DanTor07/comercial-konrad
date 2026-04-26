from ...domain.services.notifications import (
    SuscripcionSubject,
    SuscripcionEmailObserver,
    SuscripcionBAMObserver,
    SuscripcionBlockerObserver,
)
from ...models import Suscripcion as SuscripcionModel, Vendedor as VendedorModel
from ....core import constants


class GestionarSuscripcionUseCase:
    """
    Caso de uso que gestiona el ciclo de vida de la suscripcion de un vendedor.
    Usa el patron Observer (SuscripcionSubject) para notificar a:
      - SuscripcionEmailObserver  → email al vendedor
      - SuscripcionBAMObserver    → registro en auditoria/BAM
      - SuscripcionBlockerObserver → bloqueo/desbloqueo en BD
    """

    def __init__(self):
        self._subject = self._build_subject()

    def _build_subject(self) -> SuscripcionSubject:
        """Construye el Subject con los tres observadores registrados."""
        subject = SuscripcionSubject()
        subject.attach(SuscripcionEmailObserver())
        subject.attach(SuscripcionBAMObserver())
        subject.attach(SuscripcionBlockerObserver())
        return subject

    def marcar_mora(self, vendedor_id: int, dias_mora: int = 0) -> dict:
        """
        Marca la suscripcion del vendedor como en mora y notifica a todos
        los observadores (email, BAM, bloqueo).
        """
        suscripcion = SuscripcionModel.objects.filter(
            vendedor_id=vendedor_id,
            esta_activa=True
        ).first()

        if not suscripcion:
            return {'success': False, 'message': 'No se encontro suscripcion activa.'}

        suscripcion.esta_activa = False
        suscripcion.save(update_fields=['esta_activa'])

        # Publicar evento a todos los observadores
        self._subject.publicar_mora(vendedor_id, dias_mora)

        return {
            'success': True,
            'estado': constants.ESTADO_VENDEDOR_MORA,
            'message': f'Vendedor #{vendedor_id} marcado en mora.'
        }

    def reactivar(self, vendedor_id: int) -> dict:
        """
        Reactiva la suscripcion del vendedor y notifica a todos los observadores.
        """
        suscripcion = SuscripcionModel.objects.filter(
            vendedor_id=vendedor_id
        ).order_by('-fecha_inicio').first()

        if not suscripcion:
            return {'success': False, 'message': 'No se encontro suscripcion.'}

        suscripcion.esta_activa = True
        suscripcion.save(update_fields=['esta_activa'])

        self._subject.publicar_reactivacion(vendedor_id)

        return {
            'success': True,
            'estado': constants.ESTADO_VENDEDOR_ACTIVO,
            'message': f'Suscripcion del Vendedor #{vendedor_id} reactivada.'
        }

    def cancelar(self, vendedor_id: int, motivo: str = "") -> dict:
        """
        Cancela definitivamente la suscripcion y notifica a todos los observadores.
        """
        SuscripcionModel.objects.filter(vendedor_id=vendedor_id).update(esta_activa=False)

        self._subject.publicar_cancelacion(vendedor_id, motivo)

        return {
            'success': True,
            'estado': constants.ESTADO_VENDEDOR_CANCELADO,
            'message': f'Suscripcion del Vendedor #{vendedor_id} cancelada. Motivo: {motivo}'
        }

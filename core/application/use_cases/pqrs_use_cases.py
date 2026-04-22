from ...application.factories.pqrs_factory import PQRSFactory
from ...models import PQRS as PQRSModel, RespuestaPQRS


class RadicarPQRSUseCase:
    """
    Caso de uso: radicar una nueva solicitud PQRS.
    Usa PQRSFactory (Factory Method) para crear el tipo correcto.
    """

    def execute(self, tipo: str, usuario, descripcion: str) -> dict:
        solicitud = PQRSFactory.create(tipo, usuario, descripcion)
        pqrs_model = solicitud.crear_en_bd()
        return {
            'success': True,
            'pqrs_id': pqrs_model.id,
            'tipo': pqrs_model.tipo,
            'estado': pqrs_model.estado,
            'prioridad': solicitud.prioridad,
            'dias_respuesta': solicitud.dias_respuesta,
            'message': (
                f"Solicitud {pqrs_model.tipo} #{pqrs_model.id} radicada. "
                f"Tiempo máximo de respuesta: {solicitud.dias_respuesta} días hábiles."
            )
        }


class GestionarPQRSUseCase:
    """
    Caso de uso: gestión por parte del operador/gestor.
    Permite avanzar el estado (Routing Slip) y registrar respuestas.
    """

    def avanzar_estado(self, pqrs_id: int, nuevo_estado: str, gestor, respuesta_texto: str) -> dict:
        """
        Avanza la PQRS al siguiente estado y registra la respuesta del gestor.
        El método avanzar_estado() del modelo actualiza el campo ruta_estados (Routing Slip).
        """
        try:
            pqrs = PQRSModel.objects.get(id=pqrs_id)
        except PQRSModel.DoesNotExist:
            return {'success': False, 'message': f'PQRS #{pqrs_id} no encontrada.'}

        estados_validos = ['EN_GESTION', 'RESPONDIDA', 'CERRADA']
        if nuevo_estado not in estados_validos:
            return {
                'success': False,
                'message': f"Estado '{nuevo_estado}' no es válido. Use: {', '.join(estados_validos)}"
            }

        # Avanza el estado y actualiza la ruta (Routing Slip)
        pqrs.avanzar_estado(nuevo_estado)

        # Registra la respuesta del gestor
        if respuesta_texto:
            RespuestaPQRS.objects.create(
                pqrs=pqrs,
                gestor=gestor,
                respuesta=respuesta_texto
            )

        return {
            'success': True,
            'pqrs_id': pqrs_id,
            'estado': nuevo_estado,
            'ruta': pqrs.ruta_estados,
            'message': f'PQRS #{pqrs_id} avanzada a estado {nuevo_estado}.'
        }

    def listar(self, usuario=None, solo_activas: bool = True) -> list:
        """Lista PQRS del usuario o todas (para el gestor)."""
        qs = PQRSModel.objects.all().order_by('-fecha_creacion')
        if usuario:
            qs = qs.filter(usuario=usuario)
        if solo_activas:
            qs = qs.exclude(estado='CERRADA')
        return list(qs)

    def obtener(self, pqrs_id: int):
        """Obtiene una PQRS por ID con sus respuestas prefetched."""
        return (
            PQRSModel.objects
            .prefetch_related('respuestas__gestor')
            .filter(id=pqrs_id)
            .first()
        )

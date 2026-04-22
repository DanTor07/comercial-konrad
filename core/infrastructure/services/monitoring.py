from datetime import datetime
from django.db.models import Sum, Avg

from ...models import Auditoria, LogError, Pedido as PedidoModel, Vendedor as VendedorModel


class AuditService:
    @staticmethod
    def log_action(user_id: int, accion: str, detalles: str):
        Auditoria.objects.create(
            usuario_id=user_id,
            accion=accion,
            detalles=detalles
        )

    @staticmethod
    def log_error(mensaje: str, stack_trace: str):
        LogError.objects.create(
            mensaje=mensaje,
            stack_trace=stack_trace
        )


class BAMService:
    """
    Patrón: Singleton
    Garantiza una única instancia del servicio de monitoreo BAM en todo el sistema.
    Centraliza el estado de los KPIs para evitar cálculos inconsistentes cuando
    múltiples partes del sistema consultan el panel simultáneamente.

    Uso:
        bam = BAMService.get_instance()
        kpis = bam.get_kpis()
    """

    _instance = None  # La única instancia compartida

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # __init__ puede llamarse varias veces; solo inicializar una vez
        if self._initialized:
            return
        self._cache_kpis = None
        self._initialized = True

    @classmethod
    def get_instance(cls) -> 'BAMService':
        """Punto de acceso global a la instancia única."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_kpis(self) -> dict:
        """Calcula y retorna los KPIs actuales del negocio."""
        ventas = PedidoModel.objects.filter(estado="PAGADO")
        return {
            "ventas_totales": ventas.aggregate(Sum('total'))['total__sum'] or 0,
            "cantidad_pedidos": ventas.count(),
            "vendedores_activos": VendedorModel.objects.count(),
            "ticket_promedio": ventas.aggregate(Avg('total'))['total__avg'] or 0,
        }

    def invalidar_cache(self):
        """Limpia el caché de KPIs para forzar recálculo en la próxima consulta."""
        self._cache_kpis = None

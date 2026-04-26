from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Max
from django.utils import timezone
from ...models import Auditoria, LogError, Pedido as PedidoModel, Vendedor as VendedorModel, PedidoItem, ComentarioProducto, Suscripcion


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
        ahora = timezone.now()
        hace_mes = ahora - timedelta(days=30)
        hace_semana = ahora - timedelta(days=7)

        ventas = PedidoModel.objects.filter(estado="PAGADO")
        
        # Producto con mayor venta en el último mes
        top_producto = PedidoItem.objects.filter(
            pedido__estado="PAGADO", 
            pedido__fecha__gte=hace_mes
        ).values('producto__nombre').annotate(
            total_vendido=Sum('cantidad')
        ).order_by('-total_vendido').first()

        # Categoría con mayores consultas en la última semana
        top_categoria_consultas = ComentarioProducto.objects.filter(
            fecha__gte=hace_semana,
            es_pregunta=True
        ).values('producto__categoria__nombre').annotate(
            total_consultas=Count('id')
        ).order_by('-total_consultas').first()

        suscripciones = Suscripcion.objects.all()
        suscripciones_semestres = []
        
        for i in range(4):
            target_date = ahora - timedelta(days=180 * i)
            is_s1 = target_date.month <= 6
            semestre_label = f"{target_date.year}-{'S1' if is_s1 else 'S2'}"
            
            count = Suscripcion.objects.filter(
                fecha_inicio__year=target_date.year,
                fecha_inicio__month__lte=6 if is_s1 else 12,
                fecha_inicio__month__gte=1 if is_s1 else 7
            ).count()
            
            suscripciones_semestres.append({'label': semestre_label, 'count': count})

        return {
            "ventas_totales": ventas.aggregate(Sum('total'))['total__sum'] or 0,
            "cantidad_pedidos": ventas.count(),
            "vendedores_activos": VendedorModel.objects.count(),
            "ticket_promedio": ventas.aggregate(Avg('total'))['total__avg'] or 0,
            "top_producto": top_producto,
            "top_categoria": top_categoria_consultas,
            "suscripciones_semestres": reversed(suscripciones_semestres)
        }

    def invalidar_cache(self):
        """Limpia el caché de KPIs para forzar recálculo en la próxima consulta."""
        self._cache_kpis = None

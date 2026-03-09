from datetime import datetime
from ...models import Auditoria, LogError

class AuditService:
    @staticmethod
    def log_action(user_id: int, accion: str, detalles: str):
        Auditoria.objects.create(
            usuario_id=user_id,
            accion=accion,
            detalles=detalles
        )

    @staticmethod
    def log_error(codigo_error: str, mensaje: str, detalle: str):
        LogError.objects.create(
            codigo_error=codigo_error,
            mensaje=mensaje,
            detalle_tecnico=detalle
        )

class BAMService:
    @staticmethod
    def get_kpis():
        from ...models import Pedido as PedidoModel, Vendedor as VendedorModel
        from django.db.models import Sum, Avg
        
        ventas = PedidoModel.objects.filter(estado="PAGADO")
        return {
            "ventas_totales": ventas.aggregate(Sum('total'))['total__sum'] or 0,
            "cantidad_pedidos": ventas.count(),
            "vendedores_activos": VendedorModel.objects.count(),
            "ticket_promedio": ventas.aggregate(Avg('total'))['total__avg'] or 0
        }

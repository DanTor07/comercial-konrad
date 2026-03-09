from datetime import datetime
from ...models import Auditoria, LogError

class AuditService:
    @staticmethod
    def log_action(user_id: int, accion: str, tabla: str, registro_id: int, detalle: str):
        Auditoria.objects.create(
            usuario_id=user_id,
            accion=accion,
            tabla_afectada=tabla,
            registro_id=registro_id,
            detalle=detalle
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
        from django.db.models import Sum, Count, Avg
        
        return {
            "ventas_totales": PedidoModel.objects.filter(estado="PAGADO").aggregate(Sum('total'))['total__sum'] or 0,
            "cantidad_pedidos": PedidoModel.objects.filter(estado="PAGADO").count(),
            "vendedores_activos": VendedorModel.objects.count(),
            "ticket_promedio": PedidoModel.objects.filter(estado="PAGADO").aggregate(Avg('total'))['total__avg'] or 0
        }

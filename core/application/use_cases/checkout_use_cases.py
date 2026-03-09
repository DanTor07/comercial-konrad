from typing import List
from ...domain.entities.venta import Pedido, MetodoPago, Carrito
from ...domain.ports.producto_repository import ProductoRepositoryPort
from ...domain.ports.payment_port import PaymentPort

class ProcesarCheckoutUseCase:
    def __init__(self, payment_context, producto_repo: ProductoRepositoryPort, notification_service = None):
        self.payment_context = payment_context
        self.producto_repo = producto_repo
        self.notification_service = notification_service

    def execute(self, cart: Carrito, metodo_pago: MetodoPago) -> Pedido:
        if not cart.items:
            raise ValueError("El carrito está vacío")
            
        subtotal = sum(item.cantidad * item.precio_unitario for item in cart.items)
        iva = subtotal * 0.19
        total = subtotal + iva
        
        # Create Pedido domain entity
        pedido = Pedido(
            id=None,
            comprador_id=cart.comprador_id,
            items=cart.items,
            total=total,
            estado="PROCESANDO",
            metodo_pago=metodo_pago
        )
        
        # Process payment via Strategy Pattern
        success = self.payment_context.pay(pedido)
        
        if success:
            pedido.estado = "PAGADO"
            for item in cart.items:
                producto = self.producto_repo.get_by_id(item.producto_id)
                if producto:
                    producto.cantidad_disponible -= item.cantidad
                    self.producto_repo.save(producto)
            
            if self.notification_service:
                self.notification_service.notify("PEDIDO_PAGADO", {
                    "message": f"Pedido pagado con éxito",
                    "total": pedido.total,
                    "subtotal": subtotal,
                    "iva": iva
                })
        else:
            pedido.estado = "FALLIDO"
            
        return pedido

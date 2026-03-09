from ...domain.ports.payment_port import PaymentPort
from ...domain.entities.venta import Pedido, MetodoPago

class OnlinePaymentStrategy(PaymentPort):
    def process_payment(self, pedido: Pedido) -> bool:
        print(f"Procesando pago en línea para pedido {pedido.id}...")
        # Simulate interaction with banking service
        return True

    def supports(self, metodo: MetodoPago) -> bool:
        return metodo == MetodoPago.LINEA

class CreditCardStrategy(PaymentPort):
    def process_payment(self, pedido: Pedido) -> bool:
        print(f"Procesando pago con tarjeta para pedido {pedido.id}...")
        return True

    def supports(self, metodo: MetodoPago) -> bool:
        return metodo == MetodoPago.TARJETA

class ConsignmentStrategy(PaymentPort):
    def process_payment(self, pedido: Pedido) -> bool:
        print(f"Generando recibo de consignación para pedido {pedido.id}...")
        return True

    def supports(self, metodo: MetodoPago) -> bool:
        return metodo == MetodoPago.CONSIGNACION

class PaymentContext:
    def __init__(self, strategies: list[PaymentPort]):
        self.strategies = strategies

    def pay(self, pedido: Pedido) -> bool:
        for strategy in self.strategies:
            if strategy.supports(pedido.metodo_pago):
                return strategy.process_payment(pedido)
        raise ValueError(f"Método de pago {pedido.metodo_pago} no soportado")

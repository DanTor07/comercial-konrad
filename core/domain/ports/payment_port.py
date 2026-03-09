from abc import ABC, abstractmethod
from ..entities.venta import Pedido, MetodoPago

class PaymentPort(ABC):
    @abstractmethod
    def process_payment(self, pedido: Pedido) -> bool:
        pass

    @abstractmethod
    def supports(self, metodo: MetodoPago) -> bool:
        pass

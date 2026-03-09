from ...domain.entities.venta import Carrito, CarritoItem
from ...domain.ports.producto_repository import ProductoRepositoryPort

class GestionarCarritoUseCase:
    def __init__(self, producto_repo: ProductoRepositoryPort):
        self.producto_repo = producto_repo

    def agregar_producto(self, cart: Carrito, producto_id: int, cantidad: int) -> Carrito:
        producto = self.producto_repo.get_by_id(producto_id)
        if not producto:
            raise ValueError("Producto no encontrado")
        
        if producto.cantidad_disponible < cantidad:
            raise ValueError("Stock insuficiente")
            
        # Check if item exists
        for item in cart.items:
            if item.producto_id == producto_id:
                item.cantidad += cantidad
                return cart
        
        cart.items.append(CarritoItem(
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=producto.valor_unitario
        ))
        return cart

    def calcular_total(self, cart: Carrito) -> float:
        return sum(item.cantidad * item.precio_unitario for item in cart.items)

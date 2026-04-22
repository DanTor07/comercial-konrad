from django.db import transaction

from ...domain.entities.venta import Carrito, MetodoPago, Pedido
from ...domain.ports.producto_repository import ProductoRepositoryPort
from ...infrastructure.adapters.payment_strategies import PaymentContext
from ...models import Pedido as PedidoModel, PedidoItem as PedidoItemModel


class CheckoutFacade:
    """
    Patrón: Facade
    Simplifica el proceso de checkout exponiendo un único método público.
    El cliente (vista Django) no necesita conocer:
      - Cómo se valida el stock de cada ítem
      - Cómo se ejecuta el pago con el Strategy Pattern
      - Cómo se persiste el Pedido y sus ítems en BD (Transactional Client)
      - Cómo se actualiza el stock tras el pago

    Internamente coordina:
      1. Validación de stock disponible
      2. Cálculo de subtotal, IVA (19%) y total
      3. Procesamiento de pago via PaymentContext (Strategy)
      4. Persistencia atómica del Pedido en BD
      5. Actualización de stock por ítem
      6. Notificación de resultado
    """

    def __init__(
        self,
        payment_context: PaymentContext,
        producto_repo: ProductoRepositoryPort,
        notification_service=None
    ):
        self._payment_context = payment_context
        self._producto_repo = producto_repo
        self._notification_service = notification_service

    def procesar(self, cart: Carrito, metodo_pago: MetodoPago, comprador_id: int) -> dict:
        """
        Punto de entrada único del checkout.

        Returns:
            dict con claves: 'success', 'pedido_id', 'estado', 'total', 'message'
        """
        if not cart.items:
            return {'success': False, 'message': 'El carrito está vacío.'}

        # Paso 1: Validar stock
        error_stock = self._validar_stock(cart)
        if error_stock:
            return {'success': False, 'message': error_stock}

        # Paso 2: Calcular totales
        subtotal = sum(item.cantidad * item.precio_unitario for item in cart.items)
        iva = round(subtotal * 0.19, 2)
        total = round(subtotal + iva, 2)

        # Paso 3: Construir Pedido dominio y procesar pago (Strategy)
        pedido_dominio = Pedido(
            id=None,
            comprador_id=comprador_id,
            items=cart.items,
            total=total,
            estado="PROCESANDO",
            metodo_pago=metodo_pago
        )

        pago_exitoso = self._payment_context.pay(pedido_dominio)

        if not pago_exitoso:
            return {'success': False, 'message': 'El pago no pudo ser procesado. Intente nuevamente.'}

        # Paso 4: Persistir Pedido en BD de forma atómica (Transactional Client)
        pedido_id = self._persistir_pedido(cart, comprador_id, total, metodo_pago)

        # Paso 5: Actualizar stock
        self._actualizar_stock(cart)

        # Paso 6: Notificar
        if self._notification_service:
            self._notification_service.notify("PEDIDO_PAGADO", {
                "pedido_id": pedido_id,
                "total": total,
                "subtotal": subtotal,
                "iva": iva,
            })

        return {
            'success': True,
            'pedido_id': pedido_id,
            'estado': 'PAGADO',
            'total': total,
            'subtotal': subtotal,
            'iva': iva,
            'message': f'Pago procesado correctamente. Pedido #{pedido_id}.'
        }

    # ── Métodos privados de apoyo ──────────────────────────────────────────

    def _validar_stock(self, cart: Carrito) -> str:
        """
        Verifica que haya suficiente stock para cada ítem.
        Retorna un mensaje de error o cadena vacía si todo está bien.
        """
        for item in cart.items:
            producto = self._producto_repo.get_by_id(item.producto_id)
            if not producto:
                return f"Producto ID={item.producto_id} no encontrado."
            if producto.cantidad_disponible < item.cantidad:
                return (
                    f"Stock insuficiente para '{producto.nombre}'. "
                    f"Disponible: {producto.cantidad_disponible}, solicitado: {item.cantidad}."
                )
        return ""

    @transaction.atomic
    def _persistir_pedido(
        self,
        cart: Carrito,
        comprador_id: int,
        total: float,
        metodo_pago: MetodoPago
    ) -> int:
        """
        Transactional Client: crea el Pedido y todos sus PedidoItems
        en una sola transacción atómica. Si algo falla, se hace rollback completo.
        """
        pedido_model = PedidoModel.objects.create(
            comprador_id=comprador_id,
            total=total,
            metodo_pago=metodo_pago.value,
            estado="PAGADO"
        )
        for item in cart.items:
            PedidoItemModel.objects.create(
                pedido=pedido_model,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario
            )
        return pedido_model.id

    def _actualizar_stock(self, cart: Carrito) -> None:
        """Descuenta stock de cada producto después del pago exitoso."""
        for item in cart.items:
            producto = self._producto_repo.get_by_id(item.producto_id)
            if producto:
                producto.cantidad_disponible -= item.cantidad
                self._producto_repo.save(producto)

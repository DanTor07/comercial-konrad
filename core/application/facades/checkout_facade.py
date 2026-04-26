from django.db import transaction
from core import constants

from ...domain.entities.venta import Carrito, MetodoPago, Pedido
from ...domain.ports.producto_repository import ProductoRepositoryPort
from ...infrastructure.adapters.payment_strategies import PaymentContext
from ...models import (
    Pedido as PedidoModel, 
    PedidoItem as PedidoItemModel, 
    ConfiguracionSistema, 
    Producto as ProductoModel
)


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
      2. Cálculo de subtotal, IVA y total
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

    def procesar(self, cart: Carrito, metodo_pago: MetodoPago, comprador_id: int, con_domicilio: bool = False) -> dict:
        """
        Punto de entrada único del checkout.
        Calcula totales y procesa el pago.
        """
        if not cart.items:
            return {'success': False, 'message': 'El carrito está vacío.'}

        config = ConfiguracionSistema.get_config()

        # Paso 1: Validar stock
        error_stock = self._validar_stock(cart)
        if error_stock:
            return {'success': False, 'message': error_stock}

        # Paso 2: Calcular totales
        subtotal = 0
        total_comision = 0
        total_iva = 0
        peso_total = 0
        bases_domicilio = []

        for item in cart.items:
            prod_model = ProductoModel.objects.get(id=item.producto_id)
            sub_item = item.cantidad * item.precio_unitario
            subtotal += sub_item
            
            # 1. Comisión por categoría
            total_comision += sub_item * (prod_model.categoria.porcentaje_comision / 100)
            
            # 2. Peso para domicilio
            peso_total += prod_model.peso * item.cantidad
            bases_domicilio.append(prod_model.categoria.domicilio_base)
            
            # 3. IVA configurable por categoría
            if not prod_model.categoria.es_iva_incluido:
                total_iva += sub_item * prod_model.categoria.porcentaje_iva

        # Costo extra por domicilio (Ciudad y Peso)
        total_envio = 0
        if con_domicilio:
            base_domicilio = max(bases_domicilio) if bases_domicilio else 0
            total_envio = base_domicilio + (peso_total * config.costo_domicilio_por_kg)

        total_pagar = subtotal + total_comision + total_iva + total_envio

        # Paso 3: Procesar pago (Strategy)
        # Reutilizamos el objeto Pedido dominio temporal para la estrategia
        pedido_dominio = Pedido(
            id=None,
            comprador_id=comprador_id,
            items=cart.items,
            total_comision=total_comision,
            total_envio=total_envio,
            total_impuestos=total_iva,
            total_pagar=total_pagar,
            metodo_pago=metodo_pago
        )

        pago_exitoso = self._payment_context.pay(pedido_dominio)

        if not pago_exitoso:
            return {'success': False, 'message': 'El pago no pudo ser procesado. Intente nuevamente.'}

        # Paso 4: Persistir Pedido en BD (Transactional Client)
        pedido_id = self._persistir_pedido(
            cart, comprador_id, subtotal, total_comision, total_envio, total_iva, total_pagar, metodo_pago
        )

        # Paso 5: Actualizar stock
        self._actualizar_stock(cart)

        return {
            'success': True,
            'pedido_id': pedido_id,
            'estado': constants.PEDIDO_ESTADO_PAGADO,
            'total': total_pagar,
            'subtotal': subtotal,
            'comision': total_comision,
            'iva': total_iva,
            'envio': total_envio,
            'message': f'Pago procesado correctamente. Pedido #{pedido_id}.'
        }

    # ── Métodos privados de apoyo ──────────────────────────────────────────

    def _validar_stock(self, cart: Carrito) -> str:
        """
        Verifica que haya suficiente stock para cada ítem.
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
        subtotal: float,
        comision: float,
        envio: float,
        iva: float,
        total: float,
        metodo_pago: MetodoPago
    ) -> int:
        """
        Transactional Client: crea el Pedido y todos sus PedidoItems.
        """
        pedido_model = PedidoModel.objects.create(
            comprador_id=comprador_id,
            subtotal=subtotal,
            comision=comision,
            envio=envio,
            iva=iva,
            total=total,
            metodo_pago=metodo_pago.value,
            estado=constants.PEDIDO_ESTADO_PAGADO
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

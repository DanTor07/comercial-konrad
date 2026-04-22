import logging
from typing import List, Optional

from ...domain.entities.producto import Producto
from ...domain.ports.producto_repository import ProductoRepositoryPort
from ...models import Vendedor as VendedorModel

logger = logging.getLogger('audit')


class ProductoServiceProxy(ProductoRepositoryPort):
    """
    Patrón: Proxy
    Controla el acceso al repositorio de productos verificando que el vendedor
    tenga estado 'ACTIVA' antes de permitir operaciones de escritura.

    Si el vendedor está en MORA o CANCELADA, la operación save() es bloqueada
    sin llegar al repositorio real.

    Esto implementa la restricción del negocio:
    - Solo vendedores con suscripción ACTIVA pueden publicar/modificar productos.
    - Las consultas de lectura no requieren verificación de estado.

    Uso:
        repo_real  = DjangoProductoRepository()
        proxy      = ProductoServiceProxy(repo_real, vendedor_id=request.user.vendedor.id)
        use_case   = CrearProductoUseCase(proxy)
    """

    def __init__(self, repositorio: ProductoRepositoryPort, vendedor_id: int):
        self._repositorio = repositorio
        self._vendedor_id = vendedor_id

    def save(self, producto: Producto) -> Producto:
        """
        Verifica el estado del vendedor antes de delegar al repositorio real.
        Lanza PermissionError si el vendedor no está activo.
        """
        self._verificar_acceso()
        return self._repositorio.save(producto)

    def get_by_id(self, id: int) -> Optional[Producto]:
        """Lectura: sin restricción de acceso, delega directamente."""
        return self._repositorio.get_by_id(id)

    def list_all(self, criteria: dict) -> List[Producto]:
        """Lectura: sin restricción de acceso, delega directamente."""
        return self._repositorio.list_all(criteria)

    def _verificar_acceso(self):
        """
        Comprueba si el vendedor tiene suscripción activa.
        Si no, lanza PermissionError antes de llegar al repositorio real.
        """
        try:
            vendedor = VendedorModel.objects.get(id=self._vendedor_id)
        except VendedorModel.DoesNotExist:
            raise PermissionError(
                f"Vendedor #{self._vendedor_id} no encontrado."
            )

        if vendedor.estado != 'ACTIVA':
            logger.warning(
                f"[PROXY] Acceso BLOQUEADO — Vendedor #{self._vendedor_id} "
                f"tiene estado '{vendedor.estado}'. Operación save() denegada."
            )
            raise PermissionError(
                f"Tu cuenta de vendedor está en estado '{vendedor.estado}'. "
                f"Solo los vendedores con suscripción ACTIVA pueden publicar productos. "
                f"Contacta al administrador para regularizar tu situación."
            )

        logger.info(
            f"[PROXY] Acceso PERMITIDO — Vendedor #{self._vendedor_id} "
            f"estado='{vendedor.estado}'."
        )

import logging
from typing import List, Optional

from ...domain.entities.producto import Producto
from ...domain.ports.producto_repository import ProductoRepositoryPort

logger = logging.getLogger('audit')


class AuditProductoRepositoryDecorator(ProductoRepositoryPort):
    """
    Patrón: Decorator
    Envuelve cualquier implementación de ProductoRepositoryPort añadiendo
    funcionalidad de auditoría de forma transparente, sin modificar el
    repositorio original.

    El cliente inyecta este decorador en lugar del repositorio real y obtiene
    auditoría automática en cada operación de escritura (save).

        componente_real = DjangoProductoRepository()
        decorado        = AuditProductoRepositoryDecorator(componente_real)
        use_case        = CrearProductoUseCase(decorado)  # mismo contrato
    """

    def __init__(self, repositorio: ProductoRepositoryPort, usuario_id: Optional[int] = None):
        self._repositorio = repositorio
        self._usuario_id = usuario_id

    def save(self, producto: Producto) -> Producto:
        accion = "ACTUALIZAR_PRODUCTO" if producto.id else "CREAR_PRODUCTO"

        # Ejecuta la operación real en el repositorio envuelto
        resultado = self._repositorio.save(producto)

        # Añade auditoría después de la operación (comportamiento extra)
        self._registrar_auditoria(
            accion=accion,
            detalle=(
                f"Producto '{resultado.nombre}' (ID={resultado.id}) | "
                f"Stock={resultado.cantidad_disponible} | "
                f"Precio={resultado.valor_unitario}"
            )
        )
        return resultado

    def get_by_id(self, id: int) -> Optional[Producto]:
        """Lectura: no requiere auditoría, delega directamente."""
        return self._repositorio.get_by_id(id)

    def list_all(self, criteria: dict) -> List[Producto]:
        """Lectura: no requiere auditoría, delega directamente."""
        return self._repositorio.list_all(criteria)

    def _registrar_auditoria(self, accion: str, detalle: str) -> None:
        """Registra en log y en BD de auditoría."""
        logger.info(f"[AUDIT] {accion} | Usuario={self._usuario_id} | {detalle}")
        try:
            from ...infrastructure.services.monitoring import AuditService
            AuditService.log_action(self._usuario_id, accion, detalle)
        except Exception as e:
            logger.error(f"[AUDIT] Error al registrar auditoría: {e}")

from typing import List, Optional
from ...domain.entities.producto import Producto, Categoria
from ...domain.ports.producto_repository import ProductoRepositoryPort, CategoriaRepositoryPort

class ListarCategoriasUseCase:
    def __init__(self, repository: CategoriaRepositoryPort):
        self.repository = repository

    def execute(self) -> List[Categoria]:
        return self.repository.get_all()

class CrearProductoUseCase:
    def __init__(self, repository: ProductoRepositoryPort):
        self.repository = repository

    def execute(self, producto: Producto) -> Producto:
        # Business rules: validate stock, etc.
        if producto.cantidad_disponible < 0:
            raise ValueError("La cantidad disponible no puede ser negativa")
        return self.repository.save(producto)

class BuscarProductosUseCase:
    def __init__(self, repository: ProductoRepositoryPort):
        self.repository = repository

    def execute(self, criteria: dict) -> List[Producto]:
        return self.repository.list_all(criteria)

class ObtenerProductoUseCase:
    def __init__(self, repository: ProductoRepositoryPort):
        self.repository = repository

    def execute(self, producto_id: int) -> Optional[Producto]:
        return self.repository.get_by_id(producto_id)

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.producto import Producto, Categoria

class ProductoRepositoryPort(ABC):
    @abstractmethod
    def save(self, producto: Producto) -> Producto:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Producto]:
        pass

    @abstractmethod
    def list_all(self, criteria: dict) -> List[Producto]:
        pass

class CategoriaRepositoryPort(ABC):
    @abstractmethod
    def get_all(self) -> List[Categoria]:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Categoria]:
        pass

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.vendedor import Vendedor, SolicitudVendedor, SolicitudEstado

class SolicitudVendedorRepositoryPort(ABC):
    @abstractmethod
    def save(self, solicitud: SolicitudVendedor) -> SolicitudVendedor:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[SolicitudVendedor]:
        pass

    @abstractmethod
    def list_pending(self) -> List[SolicitudVendedor]:
        pass

class VendedorRepositoryPort(ABC):
    @abstractmethod
    def save(self, vendedor: Vendedor) -> Vendedor:
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Vendedor]:
        pass

    @abstractmethod
    def get_by_identificacion(self, identificacion: str) -> Optional[Vendedor]:
        pass

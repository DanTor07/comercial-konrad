from abc import ABC, abstractmethod
from enum import Enum

class CreditScore(Enum):
    BAJA = "Baja"
    ALTA = "Alta"
    ADVERTENCIA = "Advertencia"

class CreditCheckPort(ABC):
    @abstractmethod
    def check_score(self, identificacion: str) -> CreditScore:
        pass

class PoliceCheckPort(ABC):
    @abstractmethod
    def has_criminal_record(self, identificacion: str) -> bool:
        pass

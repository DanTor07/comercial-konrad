from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod


# ── Patrón Composite — Jerarquía de Categorías ────────────────────────────────

class CategoriaComponent(ABC):
    """
    Patrón: Composite — Componente abstracto.
    Define la interfaz común para nodos hoja y nodos compuestos.
    Permite tratar una categoría simple y una con subcategorías de forma uniforme.
    """

    @property
    @abstractmethod
    def nombre(self) -> str:
        pass

    @property
    @abstractmethod
    def porcentaje_comision(self) -> float:
        pass

    @property
    @abstractmethod
    def es_iva_incluido(self) -> bool:
        pass

    def agregar(self, componente: 'CategoriaComponent') -> None:
        """Solo los nodos compuestos implementan esto."""
        raise NotImplementedError("Las hojas no pueden contener hijos.")

    def get_hijos(self) -> List['CategoriaComponent']:
        """Retorna hijos si es compuesto, lista vacía si es hoja."""
        return []

    def calcular_comision(self, precio: float) -> float:
        """Calcula la comisión aplicada sobre un precio dado."""
        return precio * (self.porcentaje_comision / 100)

    def calcular_precio_con_iva(self, precio: float) -> float:
        """Retorna el precio ajustado según si el IVA ya está incluido."""
        if self.es_iva_incluido:
            return precio
        return precio * 1.19


@dataclass
class CategoriaHoja(CategoriaComponent):
    """
    Patrón: Composite — Nodo Hoja.
    Representa una categoría sin subcategorías.
    """
    id: Optional[int]
    _nombre: str
    _porcentaje_comision: float
    _es_iva_incluido: bool = True

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def porcentaje_comision(self) -> float:
        return self._porcentaje_comision

    @property
    def es_iva_incluido(self) -> bool:
        return self._es_iva_incluido


@dataclass
class CategoriaCompuesta(CategoriaComponent):
    """
    Patrón: Composite — Nodo Compuesto.
    Puede contener otras categorías (subcategorías).
    La comisión efectiva se calcula como el promedio de sus hijos.
    """
    id: Optional[int]
    _nombre: str
    _porcentaje_comision: float
    _es_iva_incluido: bool = True
    _hijos: List[CategoriaComponent] = field(default_factory=list)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def porcentaje_comision(self) -> float:
        if not self._hijos:
            return self._porcentaje_comision
        return sum(h.porcentaje_comision for h in self._hijos) / len(self._hijos)

    @property
    def es_iva_incluido(self) -> bool:
        return self._es_iva_incluido

    def agregar(self, componente: CategoriaComponent) -> None:
        self._hijos.append(componente)

    def get_hijos(self) -> List[CategoriaComponent]:
        return list(self._hijos)


# Alias de compatibilidad: el resto del sistema usa 'Categoria'
# CategoriaHoja actúa como la implementación concreta por defecto.
@dataclass
class Categoria:
    """Alias de compatibilidad con el resto del sistema (repositorios, vistas)."""
    id: Optional[int]
    nombre: str
    porcentaje_comision: float
    es_iva_incluido: bool = True

    def calcular_comision(self, precio: float) -> float:
        return precio * (self.porcentaje_comision / 100)

    def calcular_precio_con_iva(self, precio: float) -> float:
        return precio if self.es_iva_incluido else precio * 1.19

    def to_composite(self) -> CategoriaHoja:
        """Convierte esta categoría al nodo hoja del Composite."""
        return CategoriaHoja(
            id=self.id,
            _nombre=self.nombre,
            _porcentaje_comision=self.porcentaje_comision,
            _es_iva_incluido=self.es_iva_incluido
        )

@dataclass
class Producto:
    id: Optional[int]
    vendedor_id: int
    nombre: str
    categoria_id: int
    subcategoria: str
    marca: str
    es_original: bool
    color: str
    tamano: str
    peso: float
    talla: str
    es_nuevo: bool
    cantidad_disponible: int
    valor_unitario: float
    imagenes: List[str]
    caracteristicas: str

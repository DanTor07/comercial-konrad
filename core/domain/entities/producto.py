from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Categoria:
    id: Optional[int]
    nombre: str
    porcentaje_comision: float
    es_iva_incluido: bool = True

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

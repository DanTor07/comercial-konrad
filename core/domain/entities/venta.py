from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class FacturarPor(Enum):
    MENSUAL = "MENSUAL"
    SEMESTRAL = "SEMESTRAL"
    ANUAL = "ANUAL"

class PagoEstado(Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"

class MetodoPago(Enum):
    LINEA = "LINEA"
    TARJETA = "TARJETA"
    CONSIGNACION = "CONSIGNACION"

@dataclass
class Suscripcion:
    vendedor_id: int
    fecha_inicio: datetime
    fecha_fin: datetime
    tipo_facturacion: FacturarPor
    esta_activa: bool = True

@dataclass
class CarritoItem:
    producto_id: int
    cantidad: int
    precio_unitario: float

@dataclass
class Carrito:
    comprador_id: int
    items: List[CarritoItem] = field(default_factory=list)

@dataclass
class Pedido:
    id: Optional[int]
    comprador_id: int
    fecha: datetime
    items: List[CarritoItem]
    total_comision: float
    total_envio: float
    total_impuestos: float
    total_pagar: float
    metodo_pago: MetodoPago
    estado_pago: PagoEstado = PagoEstado.PENDIENTE

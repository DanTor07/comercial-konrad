from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class SolicitudEstado(Enum):
    PENDIENTE = "PENDIENTE"
    RECHAZADA = "RECHAZADA"
    DEVUELTA = "DEVUELTA"
    APROBADA = "APROBADA"

class VendedorEstado(Enum):
    PROCESO = "PROCESO"
    ACTIVA = "ACTIVA"
    EN_MORA = "EN MORA"
    CANCELADA = "CANCELADA"

@dataclass
class DocumentoAdjunto:
    tipo: str # e.g., "RUT", "Cédula", "Cámara de Comercio"
    url: str

@dataclass
class SolicitudVendedor:
    id: Optional[int]
    nombres: str
    apellidos: str
    numero_identificacion: str
    correo_electronico: str
    pais: str
    ciudad: str
    telefono: str
    documentos: List[DocumentoAdjunto]
    estado: SolicitudEstado = SolicitudEstado.PENDIENTE
    comentarios_director: Optional[str] = None

@dataclass
class Vendedor:
    id: Optional[int]
    solicitud_id: int
    numero_identificacion: str
    estado: VendedorEstado = VendedorEstado.ACTIVA
    calificacion_promedio: float = 0.0
    numero_calificaciones_bajas: int = 0

from abc import ABC, abstractmethod
from typing import Optional

from ...models import DocumentoAdjunto as DocumentoAdjuntoModel


class DocumentoAdjunto(ABC):
    """
    Patrón: Factory Method — Producto abstracto.
    Define la interfaz común para todos los documentos adjuntos.
    """

    def __init__(self, archivo):
        self.archivo = archivo

    @property
    @abstractmethod
    def tipo_label(self) -> str:
        """Etiqueta descriptiva del tipo de documento."""
        pass

    @property
    def es_requerido_siempre(self) -> bool:
        """Indica si el documento es obligatorio para todos los tipos de persona."""
        return True


# ── Productos Concretos ─────────────────────────────────────────────────────

class FotocopiaCedulaDocumento(DocumentoAdjunto):
    @property
    def tipo_label(self) -> str:
        return "Fotocopia de la cédula"


class RutDocumento(DocumentoAdjunto):
    @property
    def tipo_label(self) -> str:
        return "RUT"


class CamaraComercioDocumento(DocumentoAdjunto):
    """Solo requerido para personas jurídicas."""

    @property
    def tipo_label(self) -> str:
        return "Cámara de comercio"

    @property
    def es_requerido_siempre(self) -> bool:
        return False  # Solo para JURIDICA


class AceptacionCentralesDocumento(DocumentoAdjunto):
    @property
    def tipo_label(self) -> str:
        return "Aceptación consulta centrales de riesgo"


class AceptacionDatosDocumento(DocumentoAdjunto):
    @property
    def tipo_label(self) -> str:
        return "Aceptación tratamiento de datos personales"


# ── Factory Method ──────────────────────────────────────────────────────────

class DocumentoFactory:
    """
    Patrón: Factory Method
    Centraliza la creación de instancias de DocumentoAdjunto según el tipo.
    Desacopla el código cliente del tipo concreto de documento.
    """

    _CREATORS = {
        'fotocopia_cedula':    FotocopiaCedulaDocumento,
        'rut':                 RutDocumento,
        'camara_comercio':     CamaraComercioDocumento,
        'aceptacion_centrales': AceptacionCentralesDocumento,
        'aceptacion_datos':    AceptacionDatosDocumento,
    }

    @classmethod
    def create(cls, tipo_key: str, archivo) -> Optional[DocumentoAdjunto]:
        """
        Método de fábrica: retorna la instancia correcta de DocumentoAdjunto
        según la clave del tipo, o None si el tipo no está registrado.
        """
        creator = cls._CREATORS.get(tipo_key)
        if creator is None:
            return None
        return creator(archivo)

    @classmethod
    def create_all_from_files(cls, files_dict: dict) -> list:
        """
        Crea todos los documentos presentes en el dict de archivos.
        Solo crea instancias para los archivos que efectivamente fueron subidos.
        """
        documentos = []
        for tipo_key in cls._CREATORS:
            archivo = files_dict.get(tipo_key)
            if archivo:
                doc = cls.create(tipo_key, archivo)
                if doc:
                    documentos.append(doc)
        return documentos

    @classmethod
    def persist_documents(cls, solicitud_model, files_dict: dict):
        """
        Persiste en BD todos los documentos encontrados en files_dict.
        Usa la factory para construir cada objeto antes de guardarlo.
        """
        documentos = cls.create_all_from_files(files_dict)
        for doc in documentos:
            DocumentoAdjuntoModel.objects.create(
                solicitud=solicitud_model,
                tipo=doc.tipo_label,
                archivo=doc.archivo
            )
        return documentos

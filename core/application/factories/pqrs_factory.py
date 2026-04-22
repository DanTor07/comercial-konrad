from abc import ABC, abstractmethod

from ...models import PQRS as PQRSModel


# ── Patrón Factory Method — Producto Abstracto ────────────────────────────────

class SolicitudPQRS(ABC):
    """
    Patrón: Factory Method — Producto abstracto.
    Define la interfaz común para todos los tipos de solicitud PQRS.
    Cada subtipo concreto implementa su propia lógica de validación,
    prioridad y tiempo de respuesta según el reglamento del negocio.
    """

    def __init__(self, usuario, descripcion: str):
        self.usuario = usuario
        self.descripcion = descripcion

    @property
    @abstractmethod
    def tipo_key(self) -> str:
        """Clave del tipo: PETICION, QUEJA, RECLAMO, SUGERENCIA."""
        pass

    @property
    @abstractmethod
    def dias_respuesta(self) -> int:
        """Dias hábiles máximos de respuesta según normativa."""
        pass

    @property
    @abstractmethod
    def prioridad(self) -> str:
        """Prioridad de atención: ALTA, MEDIA, BAJA."""
        pass

    def validar(self) -> list:
        """
        Validaciones comunes. Las subclases pueden extender este método.
        Retorna lista de errores; vacía si todo es válido.
        """
        errores = []
        if not self.descripcion or len(self.descripcion.strip()) < 20:
            errores.append("La descripcion debe tener al menos 20 caracteres.")
        return errores

    def crear_en_bd(self) -> PQRSModel:
        """Persiste la solicitud en BD y retorna el modelo creado."""
        errores = self.validar()
        if errores:
            raise ValueError(f"Solicitud inválida: {', '.join(errores)}")
        return PQRSModel.objects.create(
            usuario=self.usuario,
            tipo=self.tipo_key,
            descripcion=self.descripcion,
            estado='RADICADA',
            ruta_estados='RADICADA'
        )


# ── Productos Concretos ───────────────────────────────────────────────────────

class SolicitudPeticion(SolicitudPQRS):
    """
    Petición: solicitud de información, tramite o servicio.
    Tiempo de respuesta: 15 días hábiles. Prioridad: MEDIA.
    """

    @property
    def tipo_key(self) -> str:
        return 'PETICION'

    @property
    def dias_respuesta(self) -> int:
        return 15

    @property
    def prioridad(self) -> str:
        return 'MEDIA'


class SolicitudQueja(SolicitudPQRS):
    """
    Queja: insatisfacción con la atención o servicio.
    Tiempo de respuesta: 15 días hábiles. Prioridad: MEDIA.
    """

    @property
    def tipo_key(self) -> str:
        return 'QUEJA'

    @property
    def dias_respuesta(self) -> int:
        return 15

    @property
    def prioridad(self) -> str:
        return 'MEDIA'


class SolicitudReclamo(SolicitudPQRS):
    """
    Reclamo: inconformidad con un producto o servicio recibido.
    Tiempo de respuesta: 10 días hábiles. Prioridad: ALTA.
    """

    @property
    def tipo_key(self) -> str:
        return 'RECLAMO'

    @property
    def dias_respuesta(self) -> int:
        return 10

    @property
    def prioridad(self) -> str:
        return 'ALTA'

    def validar(self) -> list:
        """El reclamo requiere descripción más detallada (mínimo 50 caracteres)."""
        errores = []
        if not self.descripcion or len(self.descripcion.strip()) < 50:
            errores.append("Un reclamo debe describir detalladamente el problema (min. 50 caracteres).")
        return errores


class SolicitudSugerencia(SolicitudPQRS):
    """
    Sugerencia: propuesta de mejora al servicio o producto.
    Tiempo de respuesta: 30 días hábiles. Prioridad: BAJA.
    """

    @property
    def tipo_key(self) -> str:
        return 'SUGERENCIA'

    @property
    def dias_respuesta(self) -> int:
        return 30

    @property
    def prioridad(self) -> str:
        return 'BAJA'


# ── Factory Method ────────────────────────────────────────────────────────────

class PQRSFactory:
    """
    Patrón: Factory Method
    Centraliza la creación de solicitudes PQRS según su tipo.
    El cliente (vista Django) solo llama a PQRSFactory.create(tipo, usuario, descripcion)
    sin conocer qué subclase concreta se instancia.

    Beneficio: agregar un nuevo tipo de PQRS solo requiere:
      1. Crear una nueva subclase de SolicitudPQRS
      2. Registrarla en _CREATORS
    """

    _CREATORS = {
        'PETICION':   SolicitudPeticion,
        'QUEJA':      SolicitudQueja,
        'RECLAMO':    SolicitudReclamo,
        'SUGERENCIA': SolicitudSugerencia,
    }

    @classmethod
    def create(cls, tipo: str, usuario, descripcion: str) -> SolicitudPQRS:
        """
        Método de fábrica principal.

        Args:
            tipo: una de las claves en _CREATORS
            usuario: instancia del User de Django
            descripcion: texto de la solicitud

        Returns:
            SolicitudPQRS del subtipo correcto

        Raises:
            ValueError si el tipo no está registrado
        """
        creator = cls._CREATORS.get(tipo.upper())
        if creator is None:
            tipos_validos = ', '.join(cls._CREATORS.keys())
            raise ValueError(
                f"Tipo de PQRS '{tipo}' no reconocido. "
                f"Tipos válidos: {tipos_validos}"
            )
        return creator(usuario=usuario, descripcion=descripcion)

    @classmethod
    def tipos_disponibles(cls) -> list:
        """Retorna la lista de tipos registrados (útil para poblar selects en UI)."""
        return list(cls._CREATORS.keys())

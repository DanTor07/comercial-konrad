from abc import ABC, abstractmethod
from typing import Optional

from ...domain.ports.external_services import CreditScore


class ValidationResult:
    """Encapsula el resultado de un eslabón de validación."""
    def __init__(self, passed: bool, reason: str = ""):
        self.passed = passed
        self.reason = reason

    def __bool__(self):
        return self.passed


class ValidationHandler(ABC):
    """
    Patrón: Chain of Responsibility
    Clase base abstracta para cada eslabón de validación.
    Cada handler decide si pasa la solicitud al siguiente o la detiene.
    """

    def __init__(self):
        self._next_handler: Optional['ValidationHandler'] = None

    def set_next(self, handler: 'ValidationHandler') -> 'ValidationHandler':
        """Encadena el siguiente handler y lo retorna para llamadas fluidas."""
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, solicitud) -> ValidationResult:
        """Procesa la validación y delega al siguiente si corresponde."""
        pass

    def _pass_to_next(self, solicitud) -> ValidationResult:
        """Delega al siguiente eslabón si existe, o aprueba por defecto."""
        if self._next_handler:
            return self._next_handler.handle(solicitud)
        return ValidationResult(True, "Validación completada exitosamente.")


class CreditScoreHandler(ValidationHandler):
    """
    Eslabón 1: Verifica el score crediticio en Datacredito y CIFIN.
    Si el score es BAJA en alguna, detiene la cadena con RECHAZADA.
    Si es ADVERTENCIA, detiene con DEVUELTA.
    Si es ALTA en ambas, pasa al siguiente eslabón.
    """

    def __init__(self, datacredito_adapter, cifin_adapter):
        super().__init__()
        self.datacredito = datacredito_adapter
        self.cifin = cifin_adapter

    def handle(self, solicitud) -> ValidationResult:
        identificacion = solicitud.numero_identificacion
        score_dc = self.datacredito.check_score(identificacion)
        score_cifin = self.cifin.check_score(identificacion)

        # Guardar resultados en la solicitud para auditoría del director
        solicitud.score_datacredito = score_dc.value
        solicitud.score_cifin = score_cifin.value
        solicitud.save(update_fields=['score_datacredito', 'score_cifin'])

        if score_dc == CreditScore.BAJA or score_cifin == CreditScore.BAJA:
            return ValidationResult(
                False,
                f"RECHAZADA: Score crediticio bajo. "
                f"Datacredito={score_dc.value}, CIFIN={score_cifin.value}."
            )

        if score_dc == CreditScore.ADVERTENCIA or score_cifin == CreditScore.ADVERTENCIA:
            return ValidationResult(
                False,
                f"DEVUELTA: Score en estado de advertencia. "
                f"Datacredito={score_dc.value}, CIFIN={score_cifin.value}. "
                f"Se requiere documentación adicional."
            )

        # Score ALTA en ambas → pasa al siguiente eslabón
        return self._pass_to_next(solicitud)


class PoliceRecordHandler(ValidationHandler):
    """
    Eslabón 2: Verifica antecedentes judiciales con la Policía Nacional.
    Si tiene antecedentes, detiene la cadena con RECHAZADA.
    Si no, pasa al siguiente eslabón.
    """

    def __init__(self, police_adapter):
        super().__init__()
        self.police = police_adapter

    def handle(self, solicitud) -> ValidationResult:
        identificacion = solicitud.numero_identificacion
        has_record = self.police.has_criminal_record(identificacion)

        # Guardar resultado en la solicitud
        solicitud.tiene_antecedentes = has_record
        solicitud.save(update_fields=['tiene_antecedentes'])

        if has_record:
            return ValidationResult(
                False,
                "RECHAZADA: El solicitante registra antecedentes judiciales."
            )

        return self._pass_to_next(solicitud)


class ManualApprovalHandler(ValidationHandler):
    """
    Eslabón 3 (final): Si llegó aquí, todas las verificaciones automáticas
    pasaron. La solicitud queda PENDIENTE para decisión manual del director.
    """

    def handle(self, solicitud) -> ValidationResult:
        return ValidationResult(
            True,
            "PENDIENTE: Verificaciones automáticas superadas. "
            "En espera de aprobación del director comercial."
        )

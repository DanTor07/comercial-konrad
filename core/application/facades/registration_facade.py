from ...application.factories.documento_factory import DocumentoFactory
from ...application.use_cases.validation_chain import (
    CreditScoreHandler, PoliceRecordHandler, ManualApprovalHandler, ValidationResult
)
from ...infrastructure.adapters.external_checks import DatacreditoAdapter, CifinAdapter, PoliceAdapter
from core import constants


class RegistrationFacade:
    """
    Patrón: Facade
    Simplifica la interfaz del subsistema de registro de vendedores.
    El cliente (vista Django) solo interactúa con esta clase, sin conocer
    los detalles de la cadena de validación, la factory de documentos ni
    el repositorio de solicitudes.

    Coordina internamente:
      1. Guardado de la solicitud via ModelForm
      2. Persistencia de documentos via DocumentoFactory (Factory Method)
      3. Ejecución de la cadena de validación automática (Chain of Responsibility)
      4. Actualización del estado según el resultado de la cadena
    """

    def __init__(self):
        self._validation_chain = self._build_validation_chain()

    def _build_validation_chain(self):
        """
        Construye y enlaza la cadena de validación:
        CreditScore → PoliceRecord → ManualApproval
        """
        credit_handler = CreditScoreHandler(DatacreditoAdapter(), CifinAdapter())
        police_handler = PoliceRecordHandler(PoliceAdapter())
        manual_handler = ManualApprovalHandler()

        credit_handler.set_next(police_handler).set_next(manual_handler)
        return credit_handler

    def process_registration(self, form, files_dict: dict) -> dict:
        """
        Punto de entrada único para el proceso de registro.

        Args:
            form: SolicitudVendedorForm ya validado (form.is_valid() == True)
            files_dict: request.FILES del request HTTP

        Returns:
            dict con claves:
              - 'success': bool
              - 'solicitud_id': int (si success)
              - 'estado': str (PENDIENTE, DEVUELTA, RECHAZADA)
              - 'message': str con el motivo
        """
        # Paso 1: Guardar la solicitud principal
        solicitud = form.save(commit=False)
        solicitud.estado = constants.ESTADO_SOLICITUD_PENDIENTE
        solicitud.save()

        # Paso 2: Persistir documentos via Factory Method
        DocumentoFactory.persist_documents(solicitud, files_dict)

        # Paso 3: Ejecutar cadena de validación automática
        resultado: ValidationResult = self._validation_chain.handle(solicitud)

        # Paso 4: Actualizar estado según resultado de la cadena
        if not resultado.passed:
            # La cadena detectó un problema automático
            if resultado.reason.startswith(constants.ESTADO_SOLICITUD_RECHAZADA):
                solicitud.estado = constants.ESTADO_SOLICITUD_RECHAZADA
                solicitud.comentarios_director = resultado.reason
            elif resultado.reason.startswith(constants.ESTADO_SOLICITUD_DEVUELTA):
                solicitud.estado = constants.ESTADO_SOLICITUD_DEVUELTA
                solicitud.comentarios_director = resultado.reason
        else:
            # Pasó todas las verificaciones automáticas → queda PENDIENTE
            solicitud.estado = constants.ESTADO_SOLICITUD_PENDIENTE
            solicitud.comentarios_director = resultado.reason

        solicitud.save(update_fields=['estado', 'comentarios_director'])

        return {
            'success': True,
            'solicitud_id': solicitud.id,
            'estado': solicitud.estado,
            'message': resultado.reason
        }

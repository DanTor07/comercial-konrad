from ...domain.entities.vendedor import SolicitudVendedor, SolicitudEstado
from ...domain.ports.vendedor_repository import SolicitudVendedorRepositoryPort
from ...domain.ports.external_services import CreditCheckPort, PoliceCheckPort, CreditScore

class RegistrarSolicitudVendedorUseCase:
    def __init__(self, repository: SolicitudVendedorRepositoryPort):
        self.repository = repository

    def execute(self, solicitud: SolicitudVendedor) -> SolicitudVendedor:
        solicitud.estado = SolicitudEstado.PENDIENTE
        return self.repository.save(solicitud)

class ProcesarDecisionSolicitudUseCase:
    def __init__(
        self, 
        repository: SolicitudVendedorRepositoryPort,
        datacredito: CreditCheckPort,
        cifin: CreditCheckPort,
        policia: PoliceCheckPort
    ):
        self.repository = repository
        self.datacredito = datacredito
        self.cifin = cifin
        self.policia = policia

    def execute(self, solicitud_id: int, decision_manual: SolicitudEstado, comentarios: str) -> SolicitudVendedor:
        solicitud = self.repository.get_by_id(solicitud_id)
        if not solicitud:
            raise ValueError("Solicitud no encontrada")

        # Perform automated checks
        score_dc = self.datacredito.check_score(solicitud.numero_identificacion)
        score_cifin = self.cifin.check_score(solicitud.numero_identificacion)
        has_record = self.policia.has_criminal_record(solicitud.numero_identificacion)

        # Business Rules for automatic transitions
        # RECHAZADA: Si su vida crediticia es Baja en alguna de las entidades o es requerida por la justicia
        if score_dc == CreditScore.BAJA or score_cifin == CreditScore.BAJA or has_record:
            solicitud.estado = SolicitudEstado.RECHAZADA
            solicitud.comentarios_director = "Automáticamente rechazada por bajo score crediticio o antecedentes."
        # DEVUELTA: Si su vida crediticia está en Advertencia
        elif score_dc == CreditScore.ADVERTENCIA or score_cifin == CreditScore.ADVERTENCIA:
            solicitud.estado = SolicitudEstado.DEVUELTA
            solicitud.comentarios_director = "Automáticamente devuelta por estado de advertencia crediticia."
        # APROBADA: Si su vida crediticia es Alta en las 2 entidades y no es requerido por la justicia
        elif score_dc == CreditScore.ALTA and score_cifin == CreditScore.ALTA and not has_record:
            solicitud.estado = SolicitudEstado.APROBADA
            solicitud.comentarios_director = "Automáticamente aprobada por excelente perfil."
        else:
            # If no automatic rule applies, use the director's manual decision
            solicitud.estado = decision_manual
            solicitud.comentarios_director = comentarios

        return self.repository.save(solicitud)

from ...domain.entities.vendedor import SolicitudVendedor, SolicitudEstado
from ...domain.ports.vendedor_repository import SolicitudVendedorRepositoryPort
from ...domain.ports.external_services import CreditCheckPort, PoliceCheckPort, CreditScore
from django.contrib.auth.models import User
from ...models import Vendedor as VendedorModel, SolicitudVendedor as SolicitudModel
from ...domain.services.notifications import SolicitudDecisionSubject, DecisionEmailObserver

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

        # Asignar la decisión manual del director
        solicitud.estado = decision_manual
        solicitud.comentarios_director = comentarios
        self.repository.save(solicitud)

        # Crear Usuario y Vendedor si la decisión es APROBADA
        extra_data = {}
        if decision_manual == SolicitudEstado.APROBADA:
            
            # Generar username y password temporal
            base_username = solicitud.correo_electronico.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=solicitud.correo_electronico,
                password=solicitud.numero_identificacion,
                first_name=solicitud.nombres,
                last_name=solicitud.apellidos
            )
            
            # Crear vendedor
            solicitud_model = SolicitudModel.objects.get(id=solicitud.id)
            VendedorModel.objects.create(
                solicitud=solicitud_model,
                usuario=user,
                estado='PROCESO'
            )
            
            extra_data = {
                'username': username,
                'password': solicitud.numero_identificacion
            }

        # Notificar a los observadores de la decisión (envío de email)
        subject = SolicitudDecisionSubject()
        subject.attach(DecisionEmailObserver())
        subject.notify_decision(solicitud, decision_manual.value, comentarios, extra_data)

        return solicitud

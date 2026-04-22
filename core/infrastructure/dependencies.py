from .repositories.vendedor_repository import DjangoSolicitudVendedorRepository, DjangoVendedorRepository
from .repositories.producto_repository import DjangoProductoRepository, DjangoCategoriaRepository
from .repositories.audit_decorator import AuditProductoRepositoryDecorator
from .repositories.producto_proxy import ProductoServiceProxy
from .adapters.external_checks import DatacreditoAdapter, CifinAdapter, PoliceAdapter
from .adapters.payment_strategies import OnlinePaymentStrategy, CreditCardStrategy, ConsignmentStrategy, PaymentContext
from .services.monitoring import BAMService
from ..application.use_cases.vendedor_use_cases import RegistrarSolicitudVendedorUseCase, ProcesarDecisionSolicitudUseCase
from ..application.use_cases.producto_use_cases import ListarCategoriasUseCase, CrearProductoUseCase, BuscarProductosUseCase, ObtenerProductoUseCase
from ..application.use_cases.carrito_use_cases import GestionarCarritoUseCase
from ..application.use_cases.checkout_use_cases import ProcesarCheckoutUseCase
from ..application.use_cases.suscripcion_use_cases import GestionarSuscripcionUseCase
from ..application.facades.checkout_facade import CheckoutFacade
from ..domain.services.notifications import Subject, EmailNotificationObserver, DashboardUpdateObserver
from ..domain.services.trends import TrendObserver

def get_registrar_solicitud_use_case():
    return RegistrarSolicitudVendedorUseCase(DjangoSolicitudVendedorRepository())

def get_procesar_decision_use_case():
    return ProcesarDecisionSolicitudUseCase(DjangoSolicitudVendedorRepository(), DatacreditoAdapter(), CifinAdapter(), PoliceAdapter())

def get_listar_categorias_use_case():
    return ListarCategoriasUseCase(DjangoCategoriaRepository())

def get_buscar_productos_use_case():
    return BuscarProductosUseCase(DjangoProductoRepository())

def get_obtener_producto_use_case():
    return ObtenerProductoUseCase(DjangoProductoRepository())

def get_crear_producto_use_case():
    return CrearProductoUseCase(DjangoProductoRepository())


def get_crear_producto_use_case_con_proxy(vendedor_id: int, usuario_id=None):
    """
    Patron: Proxy (proteccion) + Decorator (auditoria)
    Apila el Proxy sobre el Decorator sobre el repositorio real:
      DjangoProductoRepository
        -> AuditProductoRepositoryDecorator  (registra en auditoria)
          -> ProductoServiceProxy            (verifica estado del vendedor)
    El use case trabaja con la misma interfaz ProductoRepositoryPort.
    """
    repo_real = DjangoProductoRepository()
    repo_auditado = AuditProductoRepositoryDecorator(repo_real, usuario_id)
    repo_proxy = ProductoServiceProxy(repo_auditado, vendedor_id)
    return CrearProductoUseCase(repo_proxy)


def get_bam_service() -> BAMService:
    """
    Patron: Singleton
    Siempre retorna la misma instancia de BAMService.
    """
    return BAMService.get_instance()


def get_suscripcion_use_case() -> GestionarSuscripcionUseCase:
    """
    Patron: Observer
    Crea el use case de suscripcion que internamente construye
    el SuscripcionSubject con los tres observadores registrados.
    """
    return GestionarSuscripcionUseCase()

def get_notification_service():
    subject = Subject()
    subject.attach(EmailNotificationObserver())
    subject.attach(DashboardUpdateObserver())
    subject.attach(TrendObserver())
    return subject

def get_producto_repo_auditado(usuario_id=None):
    """
    Patrón: Decorator
    Retorna el repositorio de productos envuelto con auditoría transparente.
    """
    return AuditProductoRepositoryDecorator(DjangoProductoRepository(), usuario_id)


def get_checkout_facade(usuario_id=None):
    """
    Patrón: Facade
    Construye el CheckoutFacade con todas sus dependencias inyectadas.
    Usa el repositorio decorado para que las actualizaciones de stock sean auditadas.
    """
    strategies = [OnlinePaymentStrategy(), CreditCardStrategy(), ConsignmentStrategy()]
    context = PaymentContext(strategies)
    repo_auditado = get_producto_repo_auditado(usuario_id)
    return CheckoutFacade(context, repo_auditado, get_notification_service())

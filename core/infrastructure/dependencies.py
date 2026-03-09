from .repositories.vendedor_repository import DjangoSolicitudVendedorRepository, DjangoVendedorRepository
from .repositories.producto_repository import DjangoProductoRepository, DjangoCategoriaRepository
from .adapters.external_checks import DatacreditoAdapter, CifinAdapter, PoliceAdapter
from .adapters.payment_strategies import OnlinePaymentStrategy, CreditCardStrategy, ConsignmentStrategy, PaymentContext
from ..application.use_cases.vendedor_use_cases import RegistrarSolicitudVendedorUseCase, ProcesarDecisionSolicitudUseCase
from ..application.use_cases.producto_use_cases import ListarCategoriasUseCase, CrearProductoUseCase, BuscarProductosUseCase, ObtenerProductoUseCase
from ..application.use_cases.carrito_use_cases import GestionarCarritoUseCase
from ..application.use_cases.checkout_use_cases import ProcesarCheckoutUseCase
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

def get_gestionar_carrito_use_case():
    return GestionarCarritoUseCase(DjangoProductoRepository())

def get_notification_service():
    subject = Subject()
    subject.attach(EmailNotificationObserver())
    subject.attach(DashboardUpdateObserver())
    subject.attach(TrendObserver())
    return subject

def get_procesar_checkout_use_case():
    strategies = [OnlinePaymentStrategy(), CreditCardStrategy(), ConsignmentStrategy()]
    context = PaymentContext(strategies)
    return ProcesarCheckoutUseCase(context, DjangoProductoRepository(), get_notification_service())

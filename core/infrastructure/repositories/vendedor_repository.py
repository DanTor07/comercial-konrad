from typing import List, Optional
from ...domain.entities.vendedor import Vendedor, SolicitudVendedor, SolicitudEstado, DocumentoAdjunto, PersonaTipo
from ...domain.ports.vendedor_repository import VendedorRepositoryPort, SolicitudVendedorRepositoryPort
from ...models import Vendedor as VendedorModel, SolicitudVendedor as SolicitudModel, DocumentoAdjunto as DocumentoModel
from django.contrib.auth.models import User

class DjangoSolicitudVendedorRepository(SolicitudVendedorRepositoryPort):
    def save(self, solicitud: SolicitudVendedor) -> SolicitudVendedor:
        if solicitud.id:
            model = SolicitudModel.objects.get(id=solicitud.id)
            model.estado = solicitud.estado.value
            model.comentarios_director = solicitud.comentarios_director
            model.save()
        else:
            model = SolicitudModel.objects.create(
                nombres=solicitud.nombres,
                apellidos=solicitud.apellidos,
                numero_identificacion=solicitud.numero_identificacion,
                correo_electronico=solicitud.correo_electronico,
                pais=solicitud.pais,
                ciudad=solicitud.ciudad,
                telefono=solicitud.telefono,
                tipo_persona=solicitud.tipo_persona.value,
                estado=solicitud.estado.value
            )
            solicitud.id = model.id
        return solicitud

    def get_by_id(self, id: int) -> Optional[SolicitudVendedor]:
        try:
            model = SolicitudModel.objects.get(id=id)
            return self._to_entity(model)
        except SolicitudModel.DoesNotExist:
            return None

    def list_pending(self) -> List[SolicitudVendedor]:
        models = SolicitudModel.objects.filter(estado='PENDIENTE')
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: SolicitudModel) -> SolicitudVendedor:
        return SolicitudVendedor(
            id=model.id,
            nombres=model.nombres,
            apellidos=model.apellidos,
            numero_identificacion=model.numero_identificacion,
            correo_electronico=model.correo_electronico,
            pais=model.pais,
            ciudad=model.ciudad,
            telefono=model.telefono,
            tipo_persona=PersonaTipo(model.tipo_persona),
            estado=SolicitudEstado(model.estado),
            documentos=[], # Mapping files would go here
            comentarios_director=model.comentarios_director
        )

class DjangoVendedorRepository(VendedorRepositoryPort):
    def save(self, vendedor: Vendedor) -> Vendedor:
        # Implementation for saving Vendedor
        pass

    def get_by_id(self, id: int) -> Optional[Vendedor]:
        # Implementation
        pass

    def get_by_identificacion(self, identificacion: str) -> Optional[Vendedor]:
        # Implementation
        pass

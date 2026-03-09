from typing import List, Optional
from ...domain.entities.producto import Producto, Categoria
from ...domain.ports.producto_repository import ProductoRepositoryPort, CategoriaRepositoryPort
from ...models import Producto as ProductoModel, Categoria as CategoriaModel

class DjangoProductoRepository(ProductoRepositoryPort):
    def save(self, producto: Producto) -> Producto:
        if producto.id:
            model = ProductoModel.objects.get(id=producto.id)
            # Update fields...
            model.save()
        else:
            model = ProductoModel.objects.create(
                vendedor_id=producto.vendedor_id,
                nombre=producto.nombre,
                categoria_id=producto.categoria_id,
                subcategoria=producto.subcategoria,
                marca=producto.marca,
                es_original=producto.es_original,
                color=producto.color,
                tamano=producto.tamano,
                peso=producto.peso,
                talla=producto.talla,
                es_nuevo=producto.es_nuevo,
                cantidad_disponible=producto.cantidad_disponible,
                valor_unitario=producto.valor_unitario,
                caracteristicas=producto.caracteristicas
            )
            producto.id = model.id
        return producto

    def get_by_id(self, id: int) -> Optional[Producto]:
        try:
            model = ProductoModel.objects.get(id=id)
            return self._to_entity(model)
        except ProductoModel.DoesNotExist:
            return None

    def list_all(self, criteria: dict) -> List[Producto]:
        qs = ProductoModel.objects.all()
        if criteria.get('q'):
            qs = qs.filter(nombre__icontains=criteria['q'])
        if criteria.get('categoria'):
            qs = qs.filter(categoria_id=criteria['categoria'])
        
        return [self._to_entity(m) for m in qs]

    def _to_entity(self, model: ProductoModel) -> Producto:
        return Producto(
            id=model.id,
            vendedor_id=model.vendedor_id,
            nombre=model.nombre,
            categoria_id=model.categoria_id,
            subcategoria=model.subcategoria,
            marca=model.marca,
            es_original=model.es_original,
            color=model.color,
            tamano=model.tamano,
            peso=model.peso,
            talla=model.talla,
            es_nuevo=model.es_nuevo,
            cantidad_disponible=model.cantidad_disponible,
            valor_unitario=model.valor_unitario,
            imagenes=[img.imagen.url for img in model.imagenes.all()],
            caracteristicas=model.caracteristicas
        )

class DjangoCategoriaRepository(CategoriaRepositoryPort):
    def get_all(self) -> List[Categoria]:
        models = CategoriaModel.objects.all()
        return [Categoria(id=m.id, nombre=m.nombre, porcentaje_comision=m.porcentaje_comision, es_iva_incluido=m.es_iva_incluido) for m in models]

    def get_by_id(self, id: int) -> Optional[Categoria]:
        try:
            m = CategoriaModel.objects.get(id=id)
            return Categoria(id=m.id, nombre=m.nombre, porcentaje_comision=m.porcentaje_comision, es_iva_incluido=m.es_iva_incluido)
        except CategoriaModel.DoesNotExist:
            return None

from django import forms
from django.core.validators import FileExtensionValidator
from .models import SolicitudVendedor, Producto, Categoria, Comprador

class SolicitudVendedorForm(forms.ModelForm):
    pdf_validator = FileExtensionValidator(allowed_extensions=['pdf'])

    fotocopia_cedula = forms.FileField(
        label="Fotocopia de la cédula", 
        validators=[pdf_validator],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )
    rut = forms.FileField(
        label="RUT", 
        validators=[pdf_validator],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )
    camara_comercio = forms.FileField(
        label="Cámara de comercio", 
        required=False, 
        validators=[pdf_validator],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf', 'id': 'id_camara_comercio'})
    )
    aceptacion_centrales = forms.FileField(
        label="Aceptación consulta centrales", 
        validators=[pdf_validator],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )
    aceptacion_datos = forms.FileField(
        label="Aceptación tratamiento datos", 
        validators=[pdf_validator],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
    )

    class Meta:
        model = SolicitudVendedor
        fields = ['nombres', 'apellidos', 'tipo_persona', 'numero_identificacion', 'correo_electronico', 'pais', 'ciudad', 'telefono']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_persona': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_persona'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_electronico': forms.EmailInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_persona = cleaned_data.get("tipo_persona")
        camara_comercio = cleaned_data.get("camara_comercio")

        if tipo_persona == 'JURIDICA' and not camara_comercio:
            self.add_error('camara_comercio', "La Cámara de Comercio es obligatoria para personas jurídicas.")
        
        return cleaned_data

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control', 'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ProductoForm(forms.ModelForm):
    es_original = forms.TypedChoiceField(
        choices=[('True', 'Sí'), ('False', 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="¿Es original?"
    )
    es_nuevo = forms.TypedChoiceField(
        choices=[('True', 'Sí'), ('False', 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="¿Es nuevo?"
    )
    imagenes_producto = MultipleFileField(
        required=False,
        label="Imágenes del producto"
    )

    class Meta:
        model = Producto
        fields = [
            'nombre', 'categoria', 'subcategoria', 'marca', 'es_original', 
            'color', 'tamano', 'peso', 'talla', 'es_nuevo', 
            'cantidad_disponible', 'valor_unitario', 'caracteristicas'
        ]
        labels = {
            'tamano': 'Tamaño (cm)',
            'peso': 'Peso (kg)',
            'valor_unitario': 'Valor Unitario (COP)',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'subcategoria': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'tamano': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 15x10'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'talla': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad_disponible': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
            'caracteristicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'porcentaje_comision', 'es_iva_incluido']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'porcentaje_comision': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CompradorForm(forms.ModelForm):
    class Meta:
        model = Comprador
        fields = ['nombres', 'apellidos', 'numero_identificacion', 'correo_electronico', 'pais', 'ciudad', 'direccion', 'telefono', 'twitter', 'instagram']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_electronico': forms.EmailInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'twitter': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control'}),
        }
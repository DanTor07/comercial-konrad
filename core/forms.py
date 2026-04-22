from django import forms
from .models import SolicitudVendedor, Producto, Categoria

class SolicitudVendedorForm(forms.ModelForm):
    fotocopia_cedula = forms.FileField(label="Fotocopia de la cédula", widget=forms.FileInput(attrs={'class': 'form-control'}))
    rut = forms.FileField(label="RUT", widget=forms.FileInput(attrs={'class': 'form-control'}))
    camara_comercio = forms.FileField(label="Cámara de comercio", required=False, widget=forms.FileInput(attrs={'class': 'form-control', 'id': 'id_camara_comercio_row'}))
    aceptacion_centrales = forms.FileField(label="Aceptación consulta centrales", widget=forms.FileInput(attrs={'class': 'form-control'}))
    aceptacion_datos = forms.FileField(label="Aceptación tratamiento datos", widget=forms.FileInput(attrs={'class': 'form-control'}))

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

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 'categoria', 'subcategoria', 'marca', 'es_original', 
            'color', 'tamano', 'peso', 'talla', 'es_nuevo', 
            'cantidad_disponible', 'valor_unitario', 'caracteristicas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'subcategoria': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'tamano': forms.TextInput(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control'}),
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
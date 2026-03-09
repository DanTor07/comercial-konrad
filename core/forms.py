from django import forms
from .models import SolicitudVendedor, Producto, Categoria

class SolicitudVendedorForm(forms.ModelForm):
    class Meta:
        model = SolicitudVendedor
        fields = ['nombres', 'apellidos', 'numero_identificacion', 'correo_electronico', 'pais', 'ciudad', 'telefono']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o Nit'}),
            'correo_electronico': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
        }

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
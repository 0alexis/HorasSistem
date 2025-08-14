from django import forms
from django.core.exceptions import ValidationError
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    """Formulario para crear y editar empresas"""
    
    class Meta:
        model = Empresa
        # Solo campos básicos sin relaciones
        fields = ['nombre', 'nit', 'email', 'telefono', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'NIT sin puntos ni guiones'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono principal'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nombre': 'Nombre de la Empresa',
            'nit': 'NIT',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'activo': 'Empresa Activa'
        }

    def clean_nit(self):
        """Validar formato del NIT"""
        nit = self.cleaned_data.get('nit')
        if nit:
            # Limpiar el NIT de puntos y guiones
            nit_limpio = ''.join(filter(str.isdigit, nit))
            if len(nit_limpio) < 8 or len(nit_limpio) > 12:
                raise ValidationError('El NIT debe tener entre 8 y 12 dígitos.')
            
            # Verificar si ya existe otro registro con el mismo NIT
            if self.instance.pk:
                if Empresa.objects.filter(nit=nit).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Ya existe una empresa con este NIT.')
            else:
                if Empresa.objects.filter(nit=nit).exists():
                    raise ValidationError('Ya existe una empresa con este NIT.')
        
        return nit

# Formulario de búsqueda
class EmpresaFiltroForm(forms.Form):
    """Formulario para filtrar empresas"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o NIT...'
        })
    )
    activo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
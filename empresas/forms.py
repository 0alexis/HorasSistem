from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Empresa

class EmpresaForm(forms.ModelForm):
    """Formulario para crear y editar empresas"""
    
    class Meta:
        model = Empresa
        fields = ['nombre', 'nit', 'email', 'telefono', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre completo de la empresa',
                'maxlength': 200
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 900123456-1',
                'pattern': '[0-9-]+',
                'title': 'Solo números y guiones'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contacto@empresa.com.co'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +57 310 123 4567',
                'pattern': '[+0-9\s-()]+',
                'title': 'Solo números, espacios, guiones y paréntesis'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa incluyendo ciudad y departamento',
                'maxlength': 500
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'checked': True
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
        help_texts = {
            'nombre': 'Nombre oficial completo de la empresa',
            'nit': 'Número de Identificación Tributaria (sin puntos)',
            'email': 'Correo electrónico principal de contacto',
            'telefono': 'Número de teléfono principal',
            'direccion': 'Dirección fiscal completa de la empresa',
            'activo': 'Marque si la empresa está operativa y puede crear proyectos'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer obligatorios solo nombre y NIT
        self.fields['nombre'].required = True
        self.fields['nit'].required = True
        # Los demás campos son opcionales
        self.fields['email'].required = False
        self.fields['telefono'].required = False
        self.fields['direccion'].required = False

    def clean_nombre(self):
        """Validar nombre de empresa"""
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = ' '.join(nombre.split())
            if nombre.isdigit():
                raise ValidationError('El nombre de la empresa no puede ser solo números.')
            if len(nombre) < 3:
                raise ValidationError('El nombre debe tener al menos 3 caracteres.')
            
            # Verificar duplicados excluyendo la instancia actual
            if self.instance.pk:
                if Empresa.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Ya existe una empresa con este nombre.')
            else:
                if Empresa.objects.filter(nombre__iexact=nombre).exists():
                    raise ValidationError('Ya existe una empresa con este nombre.')
        return nombre

    def clean_nit(self):
        """Validar formato del NIT"""
        nit = self.cleaned_data.get('nit')
        if nit:
            nit = nit.strip()
            if not re.match(r'^\d{8,12}-?\d?$', nit):
                raise ValidationError('Formato de NIT inválido. Debe tener 8-12 dígitos seguido opcionalmente de guión y dígito verificador.')
            
            # Verificar duplicados excluyendo la instancia actual
            if self.instance.pk:
                if Empresa.objects.filter(nit=nit).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Ya existe una empresa registrada con este NIT.')
            else:
                if Empresa.objects.filter(nit=nit).exists():
                    raise ValidationError('Ya existe una empresa registrada con este NIT.')
        return nit

    def clean_email(self):
        """Validar email si se proporciona"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email

    def clean_telefono(self):
        """Validar teléfono si se proporciona"""
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            telefono = telefono.strip()
            if not re.match(r'^[+0-9\s\-()]+$', telefono):
                raise ValidationError('El teléfono contiene caracteres no válidos.')
            numeros_solo = re.sub(r'[^\d]', '', telefono)
            if len(numeros_solo) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        return telefono

# Formulario de búsqueda mejorado con redirección por NIT
class EmpresaFiltroForm(forms.Form):
    """Formulario para filtrar empresas en la lista"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, NIT o email... (NIT exacto = ir directo)',
            'style': 'border-color: #B91C1C;',
            'autocomplete': 'off',
            'title': 'Escriba un NIT completo para ir directamente al detalle'
        }),
        label='Búsqueda Rápida'
    )
    
    activo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas las empresas'),
            ('true', 'Solo activas'),
            ('false', 'Solo inactivas')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'border-color: #B91C1C;'
        }),
        label='Estado'
    )
    
    ordenar_por = forms.ChoiceField(
        required=False,
        choices=[
            ('nombre', 'Nombre A-Z'),
            ('-nombre', 'Nombre Z-A'),
            ('creado_en', 'Más antiguas'),
            ('-creado_en', 'Más recientes'),
            ('nit', 'NIT ascendente'),
            ('-nit', 'NIT descendente')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'border-color: #B91C1C;'
        }),
        label='Ordenar por',
        initial='-fecha_creacion'
    )
    
    def clean_search(self):
        """Limpiar y validar el término de búsqueda"""
        search = self.cleaned_data.get('search', '').strip()
        return search
    
    def is_nit_search(self):
        """Verificar si la búsqueda parece ser un NIT"""
        search = self.cleaned_data.get('search', '').strip()
        if search:
            # Verificar si tiene formato de NIT (números y posible guión)
            return bool(re.match(r'^\d{8,12}-?\d?$', search))
        return False
    
    def get_empresa_by_nit(self):
        """Obtener empresa por NIT exacto"""
        search = self.cleaned_data.get('search', '').strip()
        if self.is_nit_search():
            try:
                return Empresa.objects.get(nit=search)
            except Empresa.DoesNotExist:
                return None
        return None
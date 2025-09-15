from django import forms
from .models import CentroDeCosto, Tercero, CodigoTurno
from django import forms
from django.contrib.auth.models import Group, Permission
from django import forms
from django.contrib.auth.models import User, Group
from .models import Usuario
from django.utils import timezone
from django.db.models import Q 
import re
from django.core.exceptions import ValidationError



class TerceroForm(forms.ModelForm):
    class Meta:
        model = Tercero
        fields = [
            'documento', 'correo_tercero', 'nombre_tercero', 'apellido_tercero',
            'cargo_predefinido', 'centro_operativo', 'unidad_negocio',
            'centro_de_costo', 'proyecto'
        ]

class CentroDeCostoForm(forms.ModelForm):
    class Meta:
        model = CentroDeCosto
        fields = [
            'codigo', 'nombre',
        ]


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.CheckboxSelectMultiple,
        }


class CodigoTurnoForm(forms.ModelForm):
    class Meta:
        model = CodigoTurno
        fields = [
            'letra_turno',
            'tipo',
            'hora_inicio',
            'hora_final',
            'duracion_total',
            'descripcion_novedad',
            'estado_codigo'
        ]
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_final': forms.TimeInput(attrs={'type': 'time'}),
        }


class SystemUserForm(forms.ModelForm):
    """Formulario completo para crear y editar usuarios del sistema"""
    
    # Campos adicionales para contraseña
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la contraseña'
        }),
        help_text='La contraseña debe tener al menos 8 caracteres.',
        required=False
    )
    
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme la contraseña'
        }),
        required=False
    )
    
    # Campo para grupos/permisos
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label='Grupos de permisos'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'username',
            'nombre_usuario', 
            'email',
            'tercero',
            'cargo_predefinido',
            'centro_operativo',
            'is_staff',
            'is_superuser',
            'estado',
            'groups'
        ]
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario.sistema (sin espacios)',
                'id': 'id_username'
            }),
            'nombre_usuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre para mostrar en el sistema'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario@empresa.com'
            }),
            'tercero': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Seleccione un empleado...'
            }),
            'cargo_predefinido': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione un cargo...'
            }),
            'centro_operativo': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione un centro operativo...'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'username': 'Usuario del sistema *',
            'nombre_usuario': 'Nombre para mostrar',
            'email': 'Correo electrónico',
            'tercero': 'Empleado asociado *',
            'cargo_predefinido': 'Cargo',
            'centro_operativo': 'Centro operativo',
            'is_staff': '¿Es personal administrativo?',
            'is_superuser': '¿Es superusuario?',
            'estado': '¿Usuario activo?'
        }
        
        help_texts = {
            'username': 'Nombre único para iniciar sesión (solo letras, números, puntos y guiones bajos)',
            'nombre_usuario': 'Nombre que se mostrará en la interfaz del sistema',
            'email': 'Correo electrónico para notificaciones',
            'tercero': 'Empleado de la empresa que usará este usuario',
            'is_staff': 'Permite acceso al panel administrativo',
            'is_superuser': 'Acceso total al sistema (usar con precaución)',
            'estado': 'Solo usuarios activos pueden iniciar sesión'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ CORREGIR - USAR 'usuario' en lugar de 'usuario_tercero'
        # Configurar queryset para terceros que no tengan usuario asignado
        if self.instance.pk:
            # Si estamos editando, incluir el tercero actual
            self.fields['tercero'].queryset = Tercero.objects.filter(
                Q(usuario__isnull=True) | Q(pk=self.instance.tercero_id)
            ).order_by('nombre_tercero', 'apellido_tercero')
        else:
            # Si estamos creando, solo terceros sin usuario
            self.fields['tercero'].queryset = Tercero.objects.filter(
                usuario__isnull=True
            ).order_by('nombre_tercero', 'apellido_tercero')
        
        # ...resto del código igual...
        # Configurar campos opcionales para edición
        if self.instance.pk:
            # Editando usuario existente
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].help_text = 'Deje en blanco para mantener la contraseña actual'
            
            # Cargar grupos actuales
            self.fields['groups'].initial = self.instance.groups.all()
        else:
            # Creando nuevo usuario
            self.fields['password1'].required = True
            self.fields['password2'].required = True
            self.fields['estado'].initial = True  # Activo por defecto
        
        # Personalizar opciones de tercero para mostrar más información
        tercero_choices = [(None, '--- Seleccione un empleado ---')]
        for tercero in self.fields['tercero'].queryset:
            display_name = f"{tercero.nombre_tercero} {tercero.apellido_tercero}"
            if tercero.documento:
                display_name += f" - CC: {tercero.documento}"
            if tercero.correo_tercero:
                display_name += f" ({tercero.correo_tercero})"
            tercero_choices.append((tercero.pk, display_name))
        
        self.fields['tercero'].choices = tercero_choices

    def clean_username(self):
        """Validar username"""
        username = self.cleaned_data.get('username')
        if username:
            # Solo letras, números, puntos y guiones bajos
            if not re.match(r'^[a-zA-Z0-9._]+$', username):
                raise ValidationError('El nombre de usuario solo puede contener letras, números, puntos y guiones bajos.')
            
            # Verificar si ya existe (excepto el usuario actual)
            if Usuario.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este nombre de usuario ya está en uso.')
        
        return username

    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email')
        if email:
            if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_tercero(self):
        """Validar que el tercero no tenga otro usuario asignado"""
        tercero = self.cleaned_data.get('tercero')
        if tercero:
            # Verificar si el tercero ya tiene otro usuario
            existing_user = Usuario.objects.filter(tercero=tercero).exclude(pk=self.instance.pk).first()
            if existing_user:
                raise ValidationError(f'Este empleado ya tiene un usuario asignado: {existing_user.username}')
        return tercero

    def clean(self):
        """Validaciones generales del formulario"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Validar contraseñas coincidan
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')
        
        # Si es usuario nuevo, contraseña es requerida
        if not self.instance.pk and not password1:
            raise ValidationError('La contraseña es requerida para nuevos usuarios.')
        
        return cleaned_data

    def save(self, commit=True):
        """Guardar usuario con configuraciones adicionales"""
        user = super().save(commit=False)
        
        # Configurar contraseña si se proporcionó
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        
        # Configurar campos automáticos
        if not self.instance.pk:
            # Usuario nuevo
            user.fecha_creacion = timezone.now()
        
        user.fecha_actualizacion = timezone.now()
        
        if commit:
            user.save()
            
            # Asignar grupos
            if 'groups' in self.cleaned_data:
                user.groups.set(self.cleaned_data['groups'])
            
            # Guardar relaciones many-to-many
            self.save_m2m()
            
        return user


class SystemUserSearchForm(forms.Form):
    """Formulario de búsqueda para usuarios"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, usuario, email...',
            'id': 'searchInput'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('active', 'Solo activos'),
            ('inactive', 'Solo inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label='Todos los grupos',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
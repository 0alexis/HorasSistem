from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Empresa, Proyecto, CentroOperativo, CargoPredefinido, UnidadNegocio



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
    



class CargoPredefinidoForm(forms.ModelForm):
    """Formulario para crear y editar cargos predefinidos"""
    
    class Meta:
        model = CargoPredefinido
        fields = ['nombre', 'descripcion', 'salario', 'activo', 'estado_cargo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cargo',
                'maxlength': 100
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del cargo y sus responsabilidades',
                'rows': 3,
                'maxlength': 500
            }),
            'salario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'estado_cargo': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'nombre': 'Nombre del Cargo',
            'descripcion': 'Descripción',
            'salario': 'Salario Base',
            'activo': 'Mantener Cargo Activo',
            'estado_cargo': 'Estado del Cargo'
        }
        help_texts = {
            'nombre': 'Nombre identificativo del cargo predefinido',
            'descripcion': 'Descripción detallada del cargo y sus responsabilidades principales',
            'salario': 'Salario base asignado al cargo',
            'activo': 'Desmarque para inactivar este cargo predefinido',
            'estado_cargo': 'Estado actual del cargo en el sistema'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer obligatorios los campos necesarios
        self.fields['nombre'].required = True
        self.fields['descripcion'].required = False
        self.fields['salario'].required = False
        self.fields['estado_cargo'].required = False
        
        # Para CREAR: establecer activo como True por defecto y ocultarlo
        if not self.instance.pk:
            self.fields['activo'].initial = True
            self.fields['activo'].widget = forms.HiddenInput()
        else:
            # Para EDITAR: mostrar el campo normalmente
            self.fields['activo'].required = False
    
    def clean_nombre(self):
        """Validar nombre del cargo"""
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = ' '.join(nombre.split())  # Limpiar espacios extra
            if len(nombre) < 2:
                raise ValidationError('El nombre debe tener al menos 2 caracteres.')
            
            # Verificar duplicados excluyendo la instancia actual
            if self.instance.pk:
                if CargoPredefinido.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise ValidationError('Ya existe un cargo con este nombre.')
            else:
                if CargoPredefinido.objects.filter(nombre__iexact=nombre).exists():
                    raise ValidationError('Ya existe un cargo con este nombre.')
        return nombre
    
    def clean_descripcion(self):
        """Validar descripción si se proporciona"""
        descripcion = self.cleaned_data.get('descripcion')
        if descripcion:
            descripcion = descripcion.strip()
            if len(descripcion) > 500:
                raise ValidationError('La descripción no puede exceder 500 caracteres.')
        return descripcion
    
    def clean_salario(self):
        """Validar salario si se proporciona"""
        salario = self.cleaned_data.get('salario')
        if salario is not None:
            if salario < 0:
                raise ValidationError('El salario no puede ser negativo.')
            if salario > 999999999.99:
                raise ValidationError('El salario es demasiado alto.')
        return salario


class CentroOperativoForm(forms.ModelForm):
    """Formulario para crear y editar centros operativos"""
    
    class Meta:
        model = CentroOperativo
        fields = ['nombre', 'descripcion', 'direccion', 'ciudad', 'proyectos', 'promesa_valor', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del centro operativo',
                'maxlength': 200
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del centro operativo y sus funciones',
                'rows': 3,
                'maxlength': 1000
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa del centro',
                'maxlength': 200
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad donde se ubica el centro',
                'maxlength': 100
            }),
            # ✅ CAMBIAR A CHECKBOXES MÚLTIPLES
            'proyectos': forms.CheckboxSelectMultiple(attrs={
                'class': 'proyecto-checkbox'
            }),
            'promesa_valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de casetas',
                'min': '0'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nombre': 'Nombre del Centro Operativo',
            'descripcion': 'Descripción',
            'direccion': 'Dirección',
            'ciudad': 'Ciudad',
            'proyectos': 'Proyectos Asociados',
            'promesa_valor': 'PV (Cantidad de Casetas)',
            'activo': 'Centro Activo'
        }
        help_texts = {
            'nombre': 'Nombre identificativo del centro operativo',
            'descripcion': 'Descripción detallada del centro y sus funciones',
            'direccion': 'Dirección física completa del centro operativo',
            'ciudad': 'Ciudad donde se encuentra ubicado el centro',
            'proyectos': 'Seleccione los proyectos que estarán asociados a este centro operativo',
            'promesa_valor': 'Cantidad estimada de casetas o unidades',
            'activo': 'Marque si el centro está operativo y disponible'
        }


    def __init__(self, *args, **kwargs):
        # ✅ RECIBIR EL USUARIO EN EL CONSTRUCTOR
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Hacer obligatorios los campos necesarios
        self.fields['nombre'].required = True
        self.fields['direccion'].required = True
        self.fields['ciudad'].required = True
        self.fields['descripcion'].required = False
        self.fields['proyectos'].required = False
        self.fields['promesa_valor'].required = False
        
        # Para CREAR: establecer activo como True por defecto
        if not self.instance.pk:
            self.fields['activo'].initial = True
            self.fields['activo'].widget = forms.HiddenInput()
        else:
            # Para EDITAR: mostrar el campo normalmente
            self.fields['activo'].required = False
        
        # Filtrar proyectos activos
        self.fields['proyectos'].queryset = Proyecto.objects.filter(activo=True).order_by('nombre')
    
    def save(self, commit=True):
        """Sobrescribir save para asignar el usuario como responsable"""
        centro = super().save(commit=False)
        
        # ✅ ASIGNAR EL USUARIO COMO RESPONSABLE
        if self.user and not centro.responsable:
            centro.responsable = self.user
        
        if commit:
            centro.save()
            # Guardar relaciones many-to-many
            self.save_m2m()
        
        return centro

# =======================
#    FORMULARIO DE PROYECTO
# =======================

class ProyectoForm(forms.ModelForm):
    # ✅ CAMPO PERSONALIZADO CON CHECKBOXES
    centros_operativos = forms.ModelMultipleChoiceField(
        queryset=CentroOperativo.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'centro-checkbox-list'
        }),
        required=False,
        label='Centros Operativos Asociados'
    )

    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'id_empresa_proyecto', 'fecha_inicio', 'fecha_fin', 'activo']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej: Modernización Sistema de Seguridad',
                'maxlength': 200,
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'placeholder': 'Descripción detallada del proyecto, objetivos y alcance...',
                'rows': 4,
                'maxlength': 1000,
                'class': 'form-textarea'
            }),
            'id_empresa_proyecto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de empresas
        self.fields['id_empresa_proyecto'].queryset = Empresa.objects.filter(activo=True).order_by('nombre')
        self.fields['id_empresa_proyecto'].empty_label = "Seleccione una empresa..."
        
        # ✅ CONFIGURAR CENTROS OPERATIVOS
        self.fields['centros_operativos'].queryset = CentroOperativo.objects.filter(activo=True).order_by('nombre')
        
        # ✅ VALIDACIÓN ADICIONAL PARA FECHAS EN EL FRONTEND
        if self.instance and self.instance.pk:
            # Si estamos editando, preservar los valores
            if self.instance.fecha_inicio:
                self.fields['fecha_inicio'].initial = self.instance.fecha_inicio
            if self.instance.fecha_fin:
                self.fields['fecha_fin'].initial = self.instance.fecha_fin

        # ✅ SI ESTAMOS EDITANDO, CARGAR CENTROS ASOCIADOS
        if self.instance.pk:
            # Buscar centros que tienen este proyecto asociado
            centros_asociados = CentroOperativo.objects.filter(proyectos=self.instance)
            self.fields['centros_operativos'].initial = centros_asociados
        
        # Campos requeridos
        self.fields['nombre'].required = True
        self.fields['id_empresa_proyecto'].required = True
        
        # Activo por defecto
        if not self.instance.pk:
            self.fields['activo'].initial = True

    def save(self, commit=True):
        # ✅ GUARDAR EL PROYECTO PRIMERO
        proyecto = super().save(commit=commit)
        
        if commit:
            # ✅ MANEJAR CENTROS OPERATIVOS
            centros_seleccionados = self.cleaned_data.get('centros_operativos', [])
            
            # Obtener centros actualmente asociados
            centros_actuales = CentroOperativo.objects.filter(proyectos=proyecto)
            
            # Remover proyecto de centros que ya no están seleccionados
            for centro in centros_actuales:
                if centro not in centros_seleccionados:
                    centro.proyectos.remove(proyecto)
            
            # Agregar proyecto a centros recién seleccionados
            for centro in centros_seleccionados:
                if centro not in centros_actuales:
                    centro.proyectos.add(proyecto)
        
        return proyecto

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError({
                'fecha_fin': 'La fecha de finalización debe ser posterior a la fecha de inicio.'
            })

        return cleaned_data

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            queryset = Proyecto.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError('Ya existe un proyecto con este nombre.')
        
        return nombre



# =======================
#    FORMULARIO DE UNIDAD DE NEGOCIO
# =======================
#

class UnidadNegocioForm(forms.ModelForm):
    """Formulario para crear y editar unidades de negocio"""
    
    # ✅ DEFINIR CAMPOS DE FECHA EXPLÍCITAMENTE
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        input_formats=['%Y-%m-%d'],  # Formato HTML5
        label='Fecha de Inicio'
    )
    
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        input_formats=['%Y-%m-%d'],  # Formato HTML5
        label='Fecha de Fin'
    )
    
    # ✅ EMPRESAS CON CHECKBOXES
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'empresa-checkbox-list'
        }),
        required=False,
        label='Empresas Asociadas'
    )
    
    class Meta:
        model = UnidadNegocio
        fields = [
            'nombre',
            'descripcion', 
            'fecha_inicio',
            'fecha_fin',
            'activo',
            'empresas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la unidad de negocio',
                'maxlength': 200
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control form-textarea',
                'rows': 4,
                'placeholder': 'Descripción detallada de la unidad de negocio',
                'maxlength': 1000
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
            # ✅ NO incluir fecha_inicio/fecha_fin aquí (se definen arriba)
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # ✅ CONFIGURAR EMPRESAS ACTIVAS
        self.fields['empresas'].queryset = Empresa.objects.filter(activo=True).order_by('nombre')
        
        # ✅ CORRECCIÓN: USAR self.initial EN LUGAR DE self.fields[].initial
        if self.instance.pk:
            print(f"DEBUG - Editando unidad ID: {self.instance.pk}")
            print(f"DEBUG - Fecha inicio BD: {self.instance.fecha_inicio}")
            print(f"DEBUG - Fecha fin BD: {self.instance.fecha_fin}")
            
            # ✅ EMPRESAS ASOCIADAS
            empresas_asociadas = self.instance.empresas.all()
            self.initial['empresas'] = empresas_asociadas
            print(f"DEBUG - Empresas asociadas: {list(empresas_asociadas.values_list('nombre', flat=True))}")
            
            # ✅ FORMATEAR FECHAS CORRECTAMENTE
            if self.instance.fecha_inicio:
                fecha_formateada = self.instance.fecha_inicio.strftime('%Y-%m-%d')
                self.initial['fecha_inicio'] = fecha_formateada
                print(f"DEBUG - Fecha inicio formateada: {fecha_formateada}")
            else:
                print("DEBUG - No hay fecha_inicio en BD")
                
            if self.instance.fecha_fin:
                fecha_formateada = self.instance.fecha_fin.strftime('%Y-%m-%d')
                self.initial['fecha_fin'] = fecha_formateada
                print(f"DEBUG - Fecha fin formateada: {fecha_formateada}")
            else:
                print("DEBUG - No hay fecha_fin en BD")
    
        # ✅ ACTIVO POR DEFECTO AL CREAR
        if not self.instance.pk:
            self.fields['activo'].initial = True
            self.fields['activo'].widget = forms.HiddenInput()
            print("DEBUG - Creando nueva unidad")

    def clean_fecha_inicio(self):
        """Validar fecha de inicio"""
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        print(f"DEBUG - Fecha inicio limpia: {fecha_inicio}")
        return fecha_inicio

    def clean_fecha_fin(self):
        """Validar fecha de fin"""
        fecha_fin = self.cleaned_data.get('fecha_fin')
        print(f"DEBUG - Fecha fin limpia: {fecha_fin}")
        return fecha_fin

    def clean(self):
        """Validar fechas"""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError({
                'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        return cleaned_data

    def save(self, commit=True):
        """Guardar unidad con fechas y relaciones"""
        instance = super().save(commit=False)
        
        # ✅ ASEGURAR QUE LAS FECHAS SE GUARDEN
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        fecha_fin = self.cleaned_data.get('fecha_fin')
        
        if fecha_inicio is not None:
            instance.fecha_inicio = fecha_inicio
            print(f"DEBUG - Guardando fecha_inicio: {fecha_inicio}")
            
        if fecha_fin is not None:
            instance.fecha_fin = fecha_fin
            print(f"DEBUG - Guardando fecha_fin: {fecha_fin}")
        
        if commit:
            instance.save()
            # ✅ GUARDAR EMPRESAS ASOCIADAS
            empresas_seleccionadas = self.cleaned_data.get('empresas', [])
            instance.empresas.set(empresas_seleccionadas)
        
        return instance



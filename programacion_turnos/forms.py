from django import forms
from django.contrib.auth import get_user_model
from .models import Bitacora, ProgramacionHorario
from empresas.models import CentroOperativo, CargoPredefinido
from usuarios.models import Usuario
import re
from datetime import datetime, timedelta

User = get_user_model()

class ProgramacionHorarioForm(forms.ModelForm):
    class Meta:
        model = ProgramacionHorario
        fields = ['nombre', 'centro_operativo', 'modelo_turno', 'cargo_predefinido', 'fecha_inicio', 'fecha_fin',  'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_nombre'
            }),
            'centro_operativo': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_centro_operativo'
            }),
            'modelo_turno': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_modelo_turno'
            }),
            'cargo_predefinido': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_cargo_predefinido'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_fecha_inicio'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_fecha_fin'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_activo'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar las opciones de los campos
        self.fields['centro_operativo'].queryset = CentroOperativo.objects.filter(activo=True)
        self.fields['cargo_predefinido'].queryset = CargoPredefinido.objects.filter(activo=True)
        
        # Hacer algunos campos opcionales para mejor UX
       
        self.fields['activo'].initial = True

    def validar_hora_24h(self, hora):
        """Valida que la hora esté en formato 24h (HH:mm:ss)"""
        if not hora:
            return False
        
        patron = re.compile(r'^([0-1][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$')
        return bool(patron.match(hora))

    def clean_segmentos_json(self):
        segmentos = self.cleaned_data.get('segmentos_json')
        
        try:
            import json
            segmentos_list = json.loads(segmentos)
            
            for i, segmento in enumerate(segmentos_list):
                inicio = segmento.get('inicio')
                fin = segmento.get('fin')
                
                if not self.validar_hora_24h(inicio):
                    raise forms.ValidationError(
                        f'Segmento {i+1}: Hora de inicio inválida. Use formato 24h (HH:mm:ss)'
                    )
                
                if not self.validar_hora_24h(fin):
                    raise forms.ValidationError(
                        f'Segmento {i+1}: Hora de fin inválida. Use formato 24h (HH:mm:ss)'
                    )
                
            return segmentos
            
        except json.JSONDecodeError:
            raise forms.ValidationError('Error al procesar los segmentos JSON')

class BitacoraFiltrosForm(forms.Form):
    # Filtros de fecha
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Hasta'
    )
    
    # Filtro por usuario
    usuario = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="Todos los usuarios",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Usuario'
    )
    
    # Filtro por tipo de acción
    tipo_accion = forms.ChoiceField(
        choices=[('', 'Todas las acciones')] + Bitacora.TIPOS_ACCION,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Acción'
    )
    
    # Filtro por módulo
    modulo = forms.ChoiceField(
        choices=[('', 'Todos los módulos')] + Bitacora.MODULOS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Módulo'
    )
    
    # Filtro por modelo afectado
    modelo_afectado = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: ProgramacionHorario, AsignacionTurno...'
        }),
        label='Modelo Afectado'
    )
    
    # Búsqueda general
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '🔍 Buscar en descripción, IP, etc...'
        }),
        label='Búsqueda General'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer fecha por defecto (últimos 30 días)
        if not self.is_bound:
            hoy = datetime.now().date()
            hace_30_dias = hoy - timedelta(days=30)
            self.fields['fecha_desde'].initial = hace_30_dias
            self.fields['fecha_hasta'].initial = hoy


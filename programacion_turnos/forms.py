from django import forms
from .models import ProgramacionHorario
from empresas.models import CentroOperativo
from usuarios.models import Usuario
import re

class ProgramacionHorarioForm(forms.ModelForm):
    class Meta:
        model = ProgramacionHorario
        fields = ['centro_operativo', 'modelo_turno', 'fecha_inicio', 'fecha_fin', 'creado_por', 'activo']
        widgets = {
            'centro_operativo': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_centro_operativo'
            }),
            'modelo_turno': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_modelo_turno'
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
            'creado_por': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_creado_por'
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
        self.fields['creado_por'].queryset = Usuario.objects.filter(is_active=True)
        
        # Hacer algunos campos opcionales para mejor UX
        self.fields['creado_por'].required = False
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
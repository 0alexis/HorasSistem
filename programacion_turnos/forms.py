from django import forms
import re

class CodigoTurnoForm(forms.ModelForm):
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
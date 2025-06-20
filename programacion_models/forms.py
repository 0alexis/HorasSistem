from django import forms
from .models import ModeloTurno

class MatrizLetrasWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if not value:
            return "<p>La matriz se inicializará después de guardar y editar este modelo.</p>"
        html = '<table style="border-collapse: collapse;">'
        for i, fila in enumerate(value):
            html += '<tr>'
            for j, letra in enumerate(fila):
                html += (
                    f'<td style="border:1px solid #ccc;padding:2px;">'
                    f'<input type="text" name="{name}_{i}_{j}" value="{letra or ""}" size="1" maxlength="1" style="text-align:center;" />'
                    f'</td>'
                )
            html += '</tr>'
        html += '</table>'
        return html

    def value_from_datadict(self, data, files, name):
        filas = []
        i = 0
        while True:
            fila = []
            j = 0
            while True:
                key = f"{name}_{i}_{j}"
                if key in data:
                    fila.append(data[key])
                    j += 1
                else:
                    break
            if fila:
                filas.append(fila)
                i += 1
            else:
                break
        return filas

class ModeloTurnoForm(forms.ModelForm):
    class Meta:
        model = ModeloTurno
        fields = '__all__'
        widgets = {
            'matriz_letras': MatrizLetrasWidget(),
        }
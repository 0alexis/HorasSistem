from django import forms
from .models import ModeloTurno
from django.utils.safestring import mark_safe

class MatrizLetrasWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if not value:
            return mark_safe("<p>La matriz se inicializará después de guardar y editar este modelo.</p>")
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
        return mark_safe(html)

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
    matriz_letras = forms.Field(
        required=False,
        widget=MatrizLetrasWidget,
        label="Matriz de Letras"
    )

    class Meta:
        model = ModeloTurno
        fields = ['nombre', 'descripcion', 'unidad_negocio', 'tipo', 'matriz_letras']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya existe el modelo, cargar la matriz actual
        if self.instance.pk:
            letras = self.instance.letras.order_by('fila', 'columna')
            matriz = {}
            for letra in letras:
                matriz.setdefault(letra.fila, []).append(letra.valor)
            self.initial['matriz_letras'] = [matriz[k] for k in sorted(matriz.keys())]
        else:
            self.initial['matriz_letras'] = [["" for _ in range(3)] for _ in range(3)]  # Por defecto 3x3

    def save(self, commit=True):
        instance = super().save(commit=False)
        matriz = self.cleaned_data.get('matriz_letras', [])
        if commit:
            instance.save()  # Asegura que tenga un ID
            if matriz:
                # Eliminar letras anteriores
                instance.letras.all().delete()
                for fila_idx, fila in enumerate(matriz):
                    for col_idx, valor in enumerate(fila):
                        if valor:
                            instance.letras.create(fila=fila_idx, columna=col_idx, valor=valor)
        return instance
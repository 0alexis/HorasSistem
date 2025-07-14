from django import forms
from .models import ModeloTurno
from django.utils.safestring import mark_safe

class MatrizLetrasWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        # Si value es None o no es una lista, inicializa una matriz 3x3 vacía
        if not value or not isinstance(value, list):
            value = [["" for _ in range(3)] for _ in range(3)]
        html = '<table style="border-collapse: collapse;">'
        for i, fila in enumerate(value):
            html += '<tr>'
            for j, letra in enumerate(fila):
                html += (
                    f'<td style="border:1px solid #ccc;padding:2px;">'
                    f'<input type="text" name="matriz_letras_{i}_{j}" value="{letra or ""}" size="1" maxlength="1" style="text-align:center;" />'
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
                key = f"matriz_letras_{i}_{j}"
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

class MatrizLetrasField(forms.Field):
    widget = MatrizLetrasWidget

    def to_python(self, value):
        return value

    def validate(self, value):
        super().validate(value)
        # Aquí puedes agregar validaciones adicionales si quieres

class ModeloTurnoForm(forms.ModelForm):
    matriz_letras = MatrizLetrasField(label="Matriz de Letras", required=False)

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

    def clean_matriz_letras(self):
        matriz = self.cleaned_data.get('matriz_letras', [])
        if not any(any(cell for cell in fila) for fila in matriz):
            raise forms.ValidationError("Debes ingresar al menos una letra en la matriz.")
        return matriz

    def save(self, commit=True):
        instance = super().save(commit=commit)
        matriz = self.cleaned_data.get('matriz_letras', [])
        # Eliminar letras anteriores (si existen)
        if instance.pk:
            instance.letras.all().delete()
            # Crear nuevas letras
            for fila_idx, fila in enumerate(matriz):
                for col_idx, valor in enumerate(fila):
                    if valor:
                        instance.letras.create(fila=fila_idx, columna=col_idx, valor=valor)
        return instance
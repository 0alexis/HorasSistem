from django import forms
from .models import ModeloTurno
from django.utils.safestring import mark_safe
from usuarios.models import CodigoTurno

class MatrizLetrasWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if not value or not isinstance(value, list):
            value = [["" for _ in range(3)] for _ in range(3)]
        html = '''
        <style>
            .matriz-btn { margin: 4px; padding: 2px 8px; }
        </style>
        <div id="matriz-letras-container">
            <table id="matriz-letras-table" style="border-collapse: collapse;">
        '''
        for i, fila in enumerate(value):
            html += '<tr>'
            for j, letra in enumerate(fila):
                html += (
                    f'<td style="border:1px solid #ccc;padding:2px;">'
                    f'<input type="text" name="matriz_letras_{i}_{j}" value="{letra or ""}" size="1" maxlength="2" style="text-align:center;" />'
                    f'</td>'
                )
            html += '</tr>'
        html += '''
            </table>
            <button type="button" class="matriz-btn" onclick="addFila()">Agregar fila</button>
            <button type="button" class="matriz-btn" onclick="addColumna()">Agregar columna</button>
            <button type="button" class="matriz-btn" onclick="removeFila()">Eliminar fila</button>
            <button type="button" class="matriz-btn" onclick="removeColumna()">Eliminar columna</button>
        </div>
        <script>
        function addFila() {
            var table = document.getElementById('matriz-letras-table');
            var cols = table.rows[0] ? table.rows[0].cells.length : 3;
            var row = table.insertRow(-1);
            for (var j = 0; j < cols; j++) {
                var cell = row.insertCell(-1);
                cell.innerHTML = `<input type=\"text\" name=\"matriz_letras_${table.rows.length-1}_${j}\" size=\"1\" maxlength=\"2\" style=\"text-align:center;\">`;
            }
        }
        function addColumna() {
            var table = document.getElementById('matriz-letras-table');
            var rows = table.rows.length;
            var cols = rows > 0 ? table.rows[0].cells.length : 0;
            for (var i = 0; i < rows; i++) {
                var cell = table.rows[i].insertCell(-1);
                cell.innerHTML = `<input type=\"text\" name=\"matriz_letras_${i}_${cols}\" size=\"1\" maxlength=\"2\" style=\"text-align:center;\">`;
            }
        }
        function removeFila() {
            var table = document.getElementById('matriz-letras-table');
            if (table.rows.length > 1) table.deleteRow(-1);
        }
        function removeColumna() {
            var table = document.getElementById('matriz-letras-table');
            var cols = table.rows[0] ? table.rows[0].cells.length : 0;
            if (cols > 1) {
                for (var i = 0; i < table.rows.length; i++) {
                    table.rows[i].deleteCell(-1);
                }
            }
        }
        </script>
        '''
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
            letras_unicas = set()
            # Crear nuevas letras
            for fila_idx, fila in enumerate(matriz):
                for col_idx, valor in enumerate(fila):
                    if valor:
                        instance.letras.create(fila=fila_idx, columna=col_idx, valor=valor)
                        letras_unicas.add(valor)
            # Crear CodigoTurno para letras nuevas
            for letra in letras_unicas:
                if not CodigoTurno.objects.filter(letra_turno=letra).exists():
                    CodigoTurno.objects.create(letra_turno=letra, tipo='N')
        return instance
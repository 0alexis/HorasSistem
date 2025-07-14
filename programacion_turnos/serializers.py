from rest_framework import serializers
from .models import ProgramacionHorario, AsignacionTurno, ModeloTurno, LetraTurno
from datetime import timedelta

class ProgramacionHorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramacionHorario
        fields = '__all__'

class AsignacionTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionTurno
        fields = '__all__'

class ModeloTurnoSerializer(serializers.ModelSerializer):
    matriz_letras = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = ModeloTurno
        fields = ['id', 'nombre', 'descripcion', 'unidad_negocio', 'tipo', 'matriz_letras']

    def create(self, validated_data):
        matriz = validated_data.pop('matriz_letras', None)
        instance = super().create(validated_data)
        if matriz:
            for fila_idx, fila in enumerate(matriz):
                for col_idx, valor in enumerate(fila):
                    if valor:  # Solo crea si hay valor
                        LetraTurno.objects.create(
                            modelo_turno=instance,
                            fila=fila_idx,
                            columna=col_idx,
                            valor=valor
                        )
        return instance
#extender las fechas dentro de una misma programacion ya antes realizada
class ProgramacionExtensionSerializer(serializers.Serializer):
    fecha_inicio_ext = serializers.DateField()
    fecha_fin_ext = serializers.DateField()

    def validate(self, data):
        if data['fecha_inicio_ext'] > data['fecha_fin_ext']:
            raise serializers.ValidationError("La fecha de inicio debe ser anterior o igual a la fecha de fin.")
        return data

def generar_asignaciones(programacion):
    print("Entrando a generar_asignaciones")
    terceros = list(programacion.centro_operativo.terceros.all())
    print(f"Terceros encontrados: {terceros}")
    fecha_inicio = programacion.fecha_inicio
    fecha_fin = programacion.fecha_fin

    letras_qs = LetraTurno.objects.filter(modelo_turno=programacion.modelo_turno)
    print(f"Letras encontradas: {list(letras_qs)}")
    matriz = {}
    max_fila = 0
    max_col = 0

    for letra in letras_qs:
        if isinstance(letra.valor, list):
            print(f"Error: valor {letra.valor} es una lista, usando el primer elemento.")
            matriz[(letra.fila, letra.columna)] = letra.valor[0] if letra.valor else ''
        else:
            matriz[(letra.fila, letra.columna)] = letra.valor
        max_fila = max(max_fila, letra.fila)
        max_col = max(max_col, letra.columna)

    dias = (fecha_fin - fecha_inicio).days + 1
    num_terceros = len(terceros)
    print(f"Dias: {dias}, Num terceros: {num_terceros}, Max fila: {max_fila}, Max col: {max_col}")

    if num_terceros == 0 or not matriz:
        print("No hay terceros o matriz vacía, no se crean asignaciones.")
        return

    for idx, tercero in enumerate(terceros):
        fila = idx % (max_fila + 1)
        for dia_offset in range(dias):
            fecha = fecha_inicio + timedelta(days=dia_offset)
            columna = dia_offset % (max_col + 1)
            letra = matriz.get((fila, columna))
            #se prueba cambio en la parametrizacion de la columna
            #columna = dia_offset % len(fila)
            #letra = fila[columna]
            print(f"Asignando: tercero={tercero}, fecha={fecha}, letra={letra}, fila={fila}, columna={columna}")
            if letra: 
            # try: 
      #datos a guardar en la tabla, revisar      
               AsignacionTurno.objects.create(
                    programacion=programacion, #probando con ProgramacionHorario, iba programacion instanciado
                    tercero=tercero,
                    dia=fecha,
                    letra_turno=letra,
                    fila=fila,
                    columna=columna
                )
           # except Exception as e:
            #        print(f"Error al crear asignación: {e}")
           # else:
           #     print(f"Skipping invalid letra: {letra}")
    print("Fin de generar_asignaciones")

def perform_create(self, serializer):
    programacion = serializer.save()
    generar_asignaciones(programacion)
    #guardar la asignacion que se cree
    #esta presentando problemas al guardar la asignacion
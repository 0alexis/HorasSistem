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

def generar_asignaciones(programacion):
    """
    Genera las asignaciones de turnos para los terceros de un centro operativo,
    usando la matriz del modelo base y el rango de fechas de la programación.
    """
    terceros = list(programacion.centro_operativo.terceros.all())  # Ajusta según tu modelo
    matriz = programacion.modelo_turno.matriz_letras  # Matriz de letras (lista de listas)
    fecha_inicio = programacion.fecha_inicio
    fecha_fin = programacion.fecha_fin

    dias = (fecha_fin - fecha_inicio).days + 1
    num_terceros = len(terceros)
    num_filas = len(matriz)
    num_columnas = len(matriz[0]) if matriz else 0

    # Validación básica
    if num_terceros == 0 or num_filas == 0 or num_columnas == 0:
        return

    # Asignar turnos ( aqui esta la logica para la programacion de turnos en  base a los terceros de cada centro operativo)
    for idx, tercero in enumerate(terceros):
        fila = idx % num_filas  # Rota sobre las filas de la matriz
        for dia_offset in range(dias):
            fecha = fecha_inicio + timedelta(days=dia_offset)
            columna = dia_offset % num_columnas
            letra = matriz[fila][columna]
            # Crea la asignación en la base de datos
            AsignacionTurno.objects.create(
                programacion=programacion,
                tercero=tercero,
                dia=fecha,
                letra_turno=letra
            #revisar que en la base de datos no esta tomando las letras de la matriz creada como modelo base
            )

def perform_create(self, serializer):
    programacion = serializer.save()
    generar_asignaciones(programacion)
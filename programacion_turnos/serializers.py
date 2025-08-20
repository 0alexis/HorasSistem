from pyexpat.errors import messages
from django.shortcuts import redirect
from rest_framework import serializers

from programacion_turnos.forms import ProgramacionHorarioForm
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
    print(f"Centro operativo: {programacion.centro_operativo}")
    print(f"Cargo seleccionado: {programacion.cargo_predefinido}")
    
    # OBTENER TERCEROS CORRECTAMENTE
    from empresas.models import AsignacionTerceroEmpresa
    from usuarios.models import Tercero
    
    # Opción 1: Terceros asignados específicamente a este centro operativo
    asignaciones_centro = AsignacionTerceroEmpresa.objects.filter(
        centro_operativo=programacion.centro_operativo,
        activo=True
    )
    terceros_centro = [asignacion.tercero for asignacion in asignaciones_centro]
    print(f"Terceros asignados al centro: {len(terceros_centro)}")
    
    # Opción 2: Si no hay terceros específicos del centro, buscar por cargo
    if not terceros_centro:
        terceros_por_cargo = Tercero.objects.filter(
            cargo_predefinido=programacion.cargo_predefinido,
            activo=True
        )
        print(f"Terceros activos con el cargo '{programacion.cargo_predefinido}': {len(terceros_por_cargo)}")
        terceros = list(terceros_por_cargo)
    else:
        # Filtrar terceros del centro por el cargo específico
        terceros = [t for t in terceros_centro if t.cargo_predefinido_id == programacion.cargo_predefinido.id]
        print(f"Terceros del centro con cargo específico: {len(terceros)}")
    
    print(f"Terceros finales a programar: {[str(t) for t in terceros]}")
    
    if len(terceros) == 0:
        print("❌ NO HAY TERCEROS PARA PROGRAMAR")
        print("Verificar:")
        print("1. ¿Hay terceros asignados al centro operativo en AsignacionTerceroEmpresa?")
        print("2. ¿Hay terceros con el cargo seleccionado y activos?")
        print(f"3. ¿El cargo {programacion.cargo_predefinido} tiene terceros asignados?")
        return
    
    fecha_inicio = programacion.fecha_inicio
    fecha_fin = programacion.fecha_fin

    letras_qs = LetraTurno.objects.filter(modelo_turno=programacion.modelo_turno)
    print(f"Letras de turno disponibles: {[letra.letra for letra in letras_qs]}")
    
    if not letras_qs.exists():
        print("❌ NO HAY LETRAS DE TURNO PARA EL MODELO SELECCIONADO")
        return
    
    letras = list(letras_qs)
    fecha_actual = fecha_inicio
    indice_tercero = 0
    indice_letra = 0
    
    # Generar asignaciones día por día
    while fecha_actual <= fecha_fin:
        for tercero in terceros:
            letra_actual = letras[indice_letra % len(letras)]
            
            # Crear asignación
            asignacion = AsignacionTurno.objects.create(
                programacion=programacion,
                tercero=tercero,
                fecha=fecha_actual,
                letra_turno=letra_actual,
                activo=True
            )
            print(f"Creada asignación: {tercero} - {fecha_actual} - {letra_actual.letra}")
            
            indice_letra += 1
        
        fecha_actual += timedelta(days=1)
    
    print(f"✅ Programación completada desde {fecha_inicio} hasta {fecha_fin}")

def perform_create(self, serializer):
    programacion = serializer.save()
    generar_asignaciones(programacion)
    #guardar la asignacion que se cree
    #esta presentando problemas al guardar la asignacion

class CambioMallaSerializer(serializers.Serializer):
    tercero_id = serializers.IntegerField()
    fecha = serializers.DateField()
    letra = serializers.CharField(max_length=5)

class EditarMallaRequestSerializer(serializers.Serializer):
    cambios = CambioMallaSerializer(many=True)


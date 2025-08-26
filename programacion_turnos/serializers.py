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

    def create(self, validated_data):
        programacion = super().create(validated_data)
        generar_asignaciones(programacion)
        return programacion

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

class ProgramacionExtensionSerializer(serializers.Serializer):
    fecha_inicio_ext = serializers.DateField()
    fecha_fin_ext = serializers.DateField()

    def validate(self, data):
        if data['fecha_inicio_ext'] > data['fecha_fin_ext']:
            raise serializers.ValidationError("La fecha de inicio debe ser anterior o igual a la fecha de fin.")
        return data

def generar_asignaciones(programacion):
    """
    Genera asignaciones de turnos para una programación específica.
    
    Esta función:
    1. Filtra terceros del centro operativo seleccionado
    2. Solo considera terceros con el cargo predefinido específico
    3. Solo incluye terceros activos
    4. Genera asignaciones basadas en el modelo de turno
    """
    print("=== INICIANDO GENERACIÓN DE ASIGNACIONES ===")
    print(f"Programación ID: {programacion.id}")
    print(f"Centro operativo: {programacion.centro_operativo.nombre}")
    print(f"Modelo de turno: {programacion.modelo_turno.nombre}")
    print(f"Cargo predefinido: {programacion.cargo_predefinido.nombre}")
    print(f"Fechas: {programacion.fecha_inicio} - {programacion.fecha_fin}")
    
    try:
        # PASO 1: OBTENER TERCEROS DEL CENTRO OPERATIVO CON EL CARGO SELECCIONADO
        from usuarios.models import Tercero
        
        # LÓGICA CORRECTA: Buscar directamente en Tercero por centro_operativo y cargo_predefinido
        terceros_candidatos = Tercero.objects.filter(
            centro_operativo=programacion.centro_operativo,  # Centro seleccionado
            cargo_predefinido=programacion.cargo_predefinido,  # Cargo seleccionado
            estado_tercero=1  # Solo activos
        ).select_related('cargo_predefinido').order_by('apellido_tercero')
  ###MOMENTO DE REALIZAR LAS ASIGNACIONES SE REALIZA FILTRO DE NOMBRE####

        print(f"\n=== ANÁLISIS DE TERCEROS ===")
        print(f"Centro operativo seleccionado: {programacion.centro_operativo.nombre}")
        print(f"Cargo seleccionado: {programacion.cargo_predefinido.nombre}")
        print(f"Total de terceros encontrados: {terceros_candidatos.count()}")
        
        if not terceros_candidatos.exists():
            print("❌ NO HAY TERCEROS VÁLIDOS PARA LA PROGRAMACIÓN")
            print("\n🔍 DIAGNÓSTICO:")
            print("Verificar que:")
            print("1. Los terceros estén asignados al centro operativo seleccionado")
            print("2. Los terceros tengan asignado el cargo correcto")
            print("3. Los terceros estén activos (estado_tercero = 1)")
            
            # Mostrar estadísticas para debugging
            total_terceros_centro = Tercero.objects.filter(
                centro_operativo=programacion.centro_operativo
            ).count()
            
            terceros_con_cargo = Tercero.objects.filter(
                centro_operativo=programacion.centro_operativo,
                cargo_predefinido=programacion.cargo_predefinido
            ).count()
                                                                        
            terceros_activos = Tercero.objects.filter(
                centro_operativo=programacion.centro_operativo,
                estado_tercero=1
            ).count()
            
            print(f"\n📊 ESTADÍSTICAS DEL CENTRO '{programacion.centro_operativo.nombre}':")
            print(f"   - Total terceros en centro: {total_terceros_centro}")
            print(f"   - Terceros con cargo '{programacion.cargo_predefinido.nombre}': {terceros_con_cargo}")
            print(f"   - Terceros activos: {terceros_activos}")
            
            # Verificar si hay terceros con el cargo en otros centros
            terceros_cargo_total = Tercero.objects.filter(
                cargo_predefinido=programacion.cargo_predefinido,
                estado_tercero=1
            ).count()
            
            print(f"\n📊 ESTADÍSTICAS GENERALES:")
            print(f"   - Total terceros con cargo '{programacion.cargo_predefinido.nombre}' en TODA la empresa: {terceros_cargo_total}")
            
            if terceros_cargo_total > 0 and terceros_con_cargo == 0:
                print(f"\n💡 SOLUCIÓN:")
                print(f"   Hay {terceros_cargo_total} terceros con cargo '{programacion.cargo_predefinido.nombre}'")
                print(f"   pero NINGUNO está en el centro '{programacion.centro_operativo.nombre}'")
                print(f"   Verifique la asignación de centro operativo en la tabla Tercero")
            
            return
        
        # Mostrar terceros seleccionados
        print(f"\n=== TERCEROS SELECCIONADOS PARA PROGRAMACIÓN ===")
        for i, tercero in enumerate(terceros_candidatos, 1):
            print(f"   {i}. {tercero.nombre_tercero} {tercero.apellido_tercero}")
            print(f"      - Documento: {tercero.documento}")
            print(f"      - Centro: {tercero.centro_operativo.nombre}")
            print(f"      - Cargo: {tercero.cargo_predefinido.nombre}")

        # PASO 2: OBTENER LETRAS DE TURNO DEL MODELO
        letras_qs = LetraTurno.objects.filter(
            modelo_turno=programacion.modelo_turno
        ).order_by('fila', 'columna')
        
        print(f"\n=== CONFIGURACIÓN DEL MODELO DE TURNO ===")
        print(f"Letras de turno encontradas: {letras_qs.count()}")
        
        if not letras_qs.exists():
            print("❌ NO HAY LETRAS DE TURNO PARA EL MODELO SELECCIONADO")
            print("Verificar que el modelo de turno tenga letras configuradas")
            return
        
        # Construir matriz de letras
        matriz = {}
        max_fila = 0
        max_col = 0
        
        for letra in letras_qs:
            if isinstance(letra.valor, list):
                print(f"⚠️ Valor {letra.valor} es una lista, usando el primer elemento.")
                matriz[(letra.fila, letra.columna)] = letra.valor[0] if letra.valor else ''
            else:
                matriz[(letra.fila, letra.columna)] = letra.valor
            max_fila = max(max_fila, letra.fila)
            max_col = max(max_col, letra.columna)
        
        print(f"Matriz construida: {matriz}")
        print(f"Dimensiones: {max_fila + 1} filas × {max_col + 1} columnas")
        
        # PASO 3: CALCULAR PARÁMETROS DE PROGRAMACIÓN
        fecha_inicio = programacion.fecha_inicio
        fecha_fin = programacion.fecha_fin
        dias = (fecha_fin - fecha_inicio).days + 1
        num_terceros = len(terceros_candidatos)
        
        print(f"\n=== PARÁMETROS DE PROGRAMACIÓN ===")
        print(f"Rango de días: {dias} días")
        print(f"Total de terceros: {num_terceros}")
        print(f"Total de asignaciones a crear: {dias * num_terceros}")
        
        if not matriz:
            print("❌ Matriz vacía, no se crean asignaciones.")
            return
        
        # PASO 4: CREAR ASIGNACIONES
        print(f"\n=== INICIANDO CREACIÓN DE ASIGNACIONES ===")
        
        # Limpiar asignaciones existentes si las hay
        asignaciones_existentes = AsignacionTurno.objects.filter(programacion=programacion)
        if asignaciones_existentes.exists():
            print(f"⚠️ Eliminando {asignaciones_existentes.count()} asignaciones existentes...")
            asignaciones_existentes.delete()
        
        # Crear nuevas asignaciones
        asignaciones_creadas = 0
        for idx, tercero in enumerate(terceros_candidatos):
            fila = idx % (max_fila + 1)
            print(f"\n👤 Tercero {idx+1}: {tercero.nombre_tercero} {tercero.apellido_tercero} - Asignado a Fila {fila}")
            
            for dia_offset in range(dias):
                fecha = fecha_inicio + timedelta(days=dia_offset)
                columna = dia_offset % (max_col + 1)
                letra = matriz.get((fila, columna))
                
                if letra:
                    try:
                        AsignacionTurno.objects.create(
                            programacion=programacion,
                            tercero=tercero,
                            dia=fecha,
                            letra_turno=letra,
                            fila=fila,
                            columna=columna
                        )
                        asignaciones_creadas += 1
                        print(f"   ✅ {fecha.strftime('%Y-%m-%d')}: {letra}")
                    except Exception as e:
                        print(f"   ❌ Error al crear asignación: {e}")
                else:
                    print(f"   ⚠️ {fecha.strftime('%Y-%m-%d')}: Letra vacía para fila={fila}, columna={columna}")
        
        # PASO 5: VERIFICACIÓN FINAL
        total_asignaciones = AsignacionTurno.objects.filter(programacion=programacion).count()
        print(f"\n=== PROGRAMACIÓN COMPLETADA ===")
        print(f"✅ Total de asignaciones creadas: {asignaciones_creadas}")
        print(f"✅ Total de asignaciones en BD: {total_asignaciones}")
        print(f"✅ Programación exitosa para {num_terceros} terceros en {dias} días")
        
        if asignaciones_creadas != dias * num_terceros:
            print(f"⚠️ Se esperaban {dias * num_terceros} asignaciones, se crearon {asignaciones_creadas}")
        
    except Exception as e:
        print(f"❌ ERROR GENERAL EN GENERAR_ASIGNACIONES: {e}")
        import traceback
        traceback.print_exc()
        raise


class EditarLetraTurnoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    letra_turno = serializers.CharField(max_length=2)

    def validate_id(self, value):
        if not AsignacionTurno.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La asignación de turno no existe.")
        return value

    def validate_letra_turno(self, value):
        # Solo letras permitidas en la tabla LetraTurno
        if not LetraTurno.objects.filter(codigo_letra=value).exists():
            raise serializers.ValidationError("La letra de turno no es válida.")
        # Solo letras, sin números ni caracteres especiales
        if not value.isalpha():
            raise serializers.ValidationError("Solo se permiten letras para el turno.")
        return value

    def update(self, instance, validated_data):
        instance.letra_turno = validated_data['letra_turno']
        instance.save()
        return instance

    def save(self):
        id = self.validated_data['id']
        letra_turno = self.validated_data['letra_turno']
        asignacion = AsignacionTurno.objects.get(pk=id)
        self.update(asignacion, {'letra_turno': letra_turno})
        return asignacion
    


class CambioMallaSerializer(serializers.Serializer):
    tercero_id = serializers.IntegerField()
    fecha = serializers.DateField()
    letra = serializers.CharField(max_length=5)

class EditarMallaRequestSerializer(serializers.Serializer):
    cambios = CambioMallaSerializer(many=True)


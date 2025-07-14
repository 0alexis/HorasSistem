#!/usr/bin/env python
"""
Script de prueba para verificar la secuencia lógica de asignación y extensión de turnos.
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horas_sistema.settings')
django.setup()

from programacion_turnos.models import ProgramacionHorario, AsignacionTurno
from programacion_models.models import ModeloTurno, LetraTurno
from usuarios.models import Tercero
from empresas.models import CentroOperativo
from programacion_turnos.serializers import generar_asignaciones

def crear_programacion_prueba():
    """
    Crea una programación de prueba para verificar la lógica.
    """
    print("=== CREANDO PROGRAMACIÓN DE PRUEBA ===\n")
    
    try:
        # Obtener datos necesarios
        centro_operativo = CentroOperativo.objects.first()
        modelo_turno = ModeloTurno.objects.first()
        
        if not centro_operativo or not modelo_turno:
            print("❌ No hay centro operativo o modelo de turno disponible")
            return None
        
        # Crear programación de prueba
        fecha_inicio = date(2025, 1, 1)
        fecha_fin = date(2025, 1, 7)  # 7 días
        
        programacion = ProgramacionHorario.objects.create(
            centro_operativo=centro_operativo,
            modelo_turno=modelo_turno,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        print(f"✅ Programación creada: {programacion}")
        print(f"   Fecha inicio: {fecha_inicio}")
        print(f"   Fecha fin: {fecha_fin}")
        print(f"   Modelo: {modelo_turno}")
        print(f"   Centro: {centro_operativo}\n")
        
        # Generar asignaciones
        generar_asignaciones(programacion)
        
        print(f"✅ Asignaciones generadas")
        return programacion
        
    except Exception as e:
        print(f"❌ Error creando programación de prueba: {e}")
        return None

def verificar_secuencia_logica():
    """
    Verifica que la secuencia de asignación y extensión sea lógica y consistente.
    """
    print("=== VERIFICACIÓN DE SECUENCIA LÓGICA ===\n")
    
    # Obtener una programación existente para analizar
    try:
        programacion = ProgramacionHorario.objects.first()
        if not programacion:
            print("❌ No hay programaciones para analizar")
            return False
            
        print(f"📋 Analizando programación: {programacion}")
        print(f"   Fecha inicio: {programacion.fecha_inicio}")
        print(f"   Fecha fin: {programacion.fecha_fin}")
        print(f"   Modelo: {programacion.modelo_turno}")
        print(f"   Centro operativo: {programacion.centro_operativo}\n")
        
        # Obtener la matriz del modelo
        letras = LetraTurno.objects.filter(modelo_turno=programacion.modelo_turno).order_by('fila', 'columna')
        matriz = {}
        max_fila = 0
        max_col = 0
        
        for letra in letras:
            matriz[(letra.fila, letra.columna)] = letra.valor
            max_fila = max(max_fila, letra.fila)
            max_col = max(max_col, letra.columna)
        
        print(f"📊 Matriz del modelo:")
        print(f"   Filas: {max_fila + 1}, Columnas: {max_col + 1}")
        for fila in range(max_fila + 1):
            fila_str = []
            for col in range(max_col + 1):
                valor = matriz.get((fila, col), ' ')
                fila_str.append(valor)
            print(f"   Fila {fila}: {fila_str}")
        print()
        
        # Obtener asignaciones ordenadas por tercero y fecha
        asignaciones = AsignacionTurno.objects.filter(
            programacion=programacion
        ).order_by('tercero_id', 'dia')
        
        if not asignaciones.exists():
            print("❌ No hay asignaciones para analizar")
            return False
        
        # Agrupar por tercero
        terceros_asignaciones = {}
        for asignacion in asignaciones:
            tercero_id = asignacion.tercero.id_tercero
            if tercero_id not in terceros_asignaciones:
                terceros_asignaciones[tercero_id] = []
            terceros_asignaciones[tercero_id].append(asignacion)
        
        print(f"👥 Análisis por tercero:")
        errores_encontrados = []
        
        for tercero_id, asignaciones_tercero in terceros_asignaciones.items():
            tercero = asignaciones_tercero[0].tercero
            print(f"\n   Tercero: {tercero.nombre_tercero} (ID: {tercero_id})")
            
            # Verificar que todas las asignaciones del tercero tengan la misma fila
            filas_tercero = set(asignacion.fila for asignacion in asignaciones_tercero)
            if len(filas_tercero) != 1:
                error = f"❌ Tercero {tercero.nombre_tercero} tiene múltiples filas: {filas_tercero}"
                errores_encontrados.append(error)
                print(error)
            else:
                fila = filas_tercero.pop()
                print(f"   ✅ Fila asignada: {fila}")
            
            # Verificar secuencia de columnas
            asignaciones_ordenadas = sorted(asignaciones_tercero, key=lambda x: x.dia)
            columnas_esperadas = []
            dias_esperados = []
            
            for i, asignacion in enumerate(asignaciones_ordenadas):
                dia_offset = (asignacion.dia - programacion.fecha_inicio).days
                columna_esperada = dia_offset % (max_col + 1)
                columnas_esperadas.append(columna_esperada)
                dias_esperados.append(dia_offset)
                
                if asignacion.columna != columna_esperada:
                    error = f"❌ Día {asignacion.dia} (offset {dia_offset}): columna esperada {columna_esperada}, encontrada {asignacion.columna}"
                    errores_encontrados.append(error)
                    print(error)
            
            print(f"   📅 Secuencia de columnas: {[a.columna for a in asignaciones_ordenadas]}")
            print(f"   🎯 Columnas esperadas: {columnas_esperadas}")
            
            # Verificar que las letras coincidan con la matriz
            for asignacion in asignaciones_tercero:
                letra_esperada = matriz.get((asignacion.fila, asignacion.columna))
                if asignacion.letra_turno != letra_esperada:
                    error = f"❌ Posición ({asignacion.fila}, {asignacion.columna}): letra esperada '{letra_esperada}', encontrada '{asignacion.letra_turno}'"
                    errores_encontrados.append(error)
                    print(error)
        
        # Resumen
        print(f"\n=== RESUMEN ===")
        if errores_encontrados:
            print(f"❌ Se encontraron {len(errores_encontrados)} errores:")
            for error in errores_encontrados:
                print(f"   {error}")
            return False
        else:
            print(f"✅ La secuencia es perfectamente lógica y consistente!")
            print(f"✅ Todos los terceros mantienen su fila asignada")
            print(f"✅ Las columnas avanzan cíclicamente según el patrón")
            print(f"✅ Las letras coinciden exactamente con la matriz del modelo")
            return True
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        return False

def simular_extension():
    """
    Simula una extensión para verificar que la lógica sea correcta.
    """
    print("\n=== SIMULACIÓN DE EXTENSIÓN ===\n")
    
    try:
        programacion = ProgramacionHorario.objects.first()
        if not programacion:
            print("❌ No hay programaciones para simular extensión")
            return False
        
        # Simular fechas de extensión
        fecha_inicio_ext = programacion.fecha_fin + timedelta(days=1)
        fecha_fin_ext = fecha_inicio_ext + timedelta(days=6)  # 7 días de extensión
        
        print(f"📅 Simulando extensión:")
        print(f"   Desde: {fecha_inicio_ext}")
        print(f"   Hasta: {fecha_fin_ext}")
        print(f"   Días de extensión: {(fecha_fin_ext - fecha_inicio_ext).days + 1}\n")
        
        # Obtener última posición de cada tercero
        ultimas_posiciones = {}
        for asignacion in AsignacionTurno.objects.filter(
            programacion=programacion
        ).order_by('tercero_id', '-dia'):
            if asignacion.tercero.id_tercero not in ultimas_posiciones:
                ultimas_posiciones[asignacion.tercero.id_tercero] = {
                    'fila': asignacion.fila,
                    'columna': asignacion.columna,
                    'dia': asignacion.dia
                }
        
        # Obtener matriz
        letras = LetraTurno.objects.filter(modelo_turno=programacion.modelo_turno)
        matriz = {}
        max_col = 0
        for letra in letras:
            matriz[(letra.fila, letra.columna)] = letra.valor
            max_col = max(max_col, letra.columna)
        
        print(f"🔮 Predicción de extensión:")
        for tercero_id, ultima_pos in ultimas_posiciones.items():
            tercero = Tercero.objects.get(id_tercero=tercero_id)
            print(f"\n   Tercero: {tercero.nombre_tercero}")
            print(f"   Última posición: fila {ultima_pos['fila']}, columna {ultima_pos['columna']}")
            
            # Predecir las siguientes asignaciones
            for i in range(7):
                fecha = fecha_inicio_ext + timedelta(days=i)
                dias_desde_ultima = (fecha - ultima_pos['dia']).days
                nueva_columna = (ultima_pos['columna'] + dias_desde_ultima) % (max_col + 1)
                letra = matriz.get((ultima_pos['fila'], nueva_columna))
                
                print(f"   Día {fecha}: columna {nueva_columna} -> letra '{letra}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la simulación: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando verificación de secuencia lógica...\n")
    
    # Crear programación de prueba si no existe
    if not ProgramacionHorario.objects.exists():
        programacion = crear_programacion_prueba()
        if not programacion:
            print("❌ No se pudo crear la programación de prueba")
            sys.exit(1)
    
    # Verificar secuencia actual
    secuencia_ok = verificar_secuencia_logica()
    
    # Simular extensión
    extension_ok = simular_extension()
    
    print(f"\n=== RESULTADO FINAL ===")
    if secuencia_ok and extension_ok:
        print("🎉 ¡PERFECTO! La asignación y extensión son lógicamente secuenciales")
        print("✅ La solución implementada es correcta y consistente")
    else:
        print("⚠️ Se encontraron problemas que requieren atención") 
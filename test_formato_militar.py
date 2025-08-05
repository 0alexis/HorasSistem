#!/usr/bin/env python3
"""
Script de prueba para el formato militar en códigos de turno
"""

import re
from datetime import datetime
import json

def validar_hora_militar(hora_str):
    """
    Validar y corregir formato de hora militar (00:00 a 23:59)
    """
    if not hora_str:
        return None
    
    # Convertir de formato 12 horas a militar si es necesario
    if 'AM' in hora_str or 'PM' in hora_str:
        try:
            # Parsear el tiempo en formato 12 horas
            tiempo_obj = datetime.strptime(hora_str, '%I:%M %p')
            # Convertir a formato militar
            hora_str = tiempo_obj.strftime('%H:%M')
            print(f"🔄 Convertido: {hora_str}")
        except Exception as e:
            print(f"❌ Error al convertir: {e}")
            return None
    
    # Validar formato militar HH:MM con regex específico
    regex_militar = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    if regex_militar.match(hora_str):
        try:
            horas, minutos = hora_str.split(':')
            hora_num = int(horas)
            minuto_num = int(minutos)
            
            # Validar rango militar (00:00 a 23:59)
            if 0 <= hora_num <= 23 and 0 <= minuto_num <= 59:
                resultado = f"{hora_num:02d}:{minuto_num:02d}"
                print(f"✅ Formato militar válido: {resultado}")
                return resultado
            else:
                print(f"❌ Rango inválido: {hora_str}")
                return None
        except Exception as e:
            print(f"❌ Error al procesar: {e}")
            return None
    else:
        print(f"❌ Formato inválido: {hora_str}")
        return None

def convertir_a_militar(tiempo_12h):
    """
    Convertir formato 12 horas a militar
    """
    try:
        # Parsear el tiempo en formato 12 horas
        tiempo_obj = datetime.strptime(tiempo_12h, '%I:%M %p')
        # Convertir a formato militar
        return tiempo_obj.strftime('%H:%M')
    except Exception as e:
        print(f"❌ Error al convertir: {e}")
        return tiempo_12h

def probar_validaciones():
    """
    Probar diferentes casos de validación
    """
    print("🧪 PRUEBAS DE FORMATO MILITAR")
    print("=" * 50)
    
    # Casos de prueba
    casos_prueba = [
        # Formato militar correcto
        ("00:00", "Medianoche"),
        ("06:30", "Mañana"),
        ("12:00", "Mediodía"),
        ("18:45", "Tarde"),
        ("23:59", "Noche"),
        
        # Formato 12 horas
        ("12:00 AM", "Medianoche 12h"),
        ("6:30 AM", "Mañana 12h"),
        ("12:00 PM", "Mediodía 12h"),
        ("6:45 PM", "Tarde 12h"),
        ("11:59 PM", "Noche 12h"),
        
        # Casos inválidos
        ("24:00", "Hora inválida"),
        ("12:60", "Minutos inválidos"),
        ("25:30", "Hora fuera de rango"),
        ("abc", "Texto inválido"),
        ("", "Vacío"),
    ]
    
    resultados = []
    
    for hora, descripcion in casos_prueba:
        print(f"\n📝 Probando: {hora} ({descripcion})")
        resultado = validar_hora_militar(hora)
        resultados.append({
            'entrada': hora,
            'descripcion': descripcion,
            'resultado': resultado,
            'valido': resultado is not None
        })
    
    return resultados

def probar_segmentos():
    """
    Probar validación de segmentos completos
    """
    print("\n\n📋 PRUEBAS DE SEGMENTOS")
    print("=" * 50)
    
    segmentos_prueba = [
        # Segmentos válidos
        {
            'nombre': 'Turno Normal',
            'segmentos': [
                {'inicio': '08:00', 'fin': '16:00', 'tipo': 'NORMAL'}
            ]
        },
        {
            'nombre': 'Turno Festivo',
            'segmentos': [
                {'inicio': '08:00', 'fin': '12:00', 'tipo': 'NORMAL'},
                {'inicio': '12:00', 'fin': '18:00', 'tipo': 'FESTIVO'}
            ]
        },
        {
            'nombre': 'Turno Nocturno',
            'segmentos': [
                {'inicio': '22:00', 'fin': '06:00', 'tipo': 'NOCTURNO'}
            ]
        },
        
        # Segmentos con errores
        {
            'nombre': 'Turno con Error',
            'segmentos': [
                {'inicio': '08:00', 'fin': '16:00', 'tipo': 'NORMAL'},
                {'inicio': '16:00', 'fin': '25:00', 'tipo': 'FESTIVO'}  # Hora inválida
            ]
        },
        {
            'nombre': 'Turno con Formato 12h',
            'segmentos': [
                {'inicio': '8:00 AM', 'fin': '4:00 PM', 'tipo': 'NORMAL'}
            ]
        }
    ]
    
    for turno in segmentos_prueba:
        print(f"\n📋 {turno['nombre']}:")
        
        errores = []
        for i, segmento in enumerate(turno['segmentos']):
            print(f"  Segmento {i+1}:")
            
            # Validar inicio
            inicio_valido = validar_hora_militar(segmento['inicio'])
            if inicio_valido:
                print(f"    ✅ Inicio: {inicio_valido}")
            else:
                print(f"    ❌ Inicio inválido: {segmento['inicio']}")
                errores.append(f"Segmento {i+1} inicio inválido")
            
            # Validar fin
            fin_valido = validar_hora_militar(segmento['fin'])
            if fin_valido:
                print(f"    ✅ Fin: {fin_valido}")
            else:
                print(f"    ❌ Fin inválido: {segmento['fin']}")
                errores.append(f"Segmento {i+1} fin inválido")
            
            # Validar tipo
            tipos_validos = ['NORMAL', 'FESTIVO', 'NOCTURNO', 'DOMINGO', 'EXTRA', 'COMPENSATORIO']
            if segmento['tipo'] in tipos_validos:
                print(f"    ✅ Tipo: {segmento['tipo']}")
            else:
                print(f"    ❌ Tipo inválido: {segmento['tipo']}")
                errores.append(f"Segmento {i+1} tipo inválido")
        
        if errores:
            print(f"  ❌ Errores encontrados: {len(errores)}")
            for error in errores:
                print(f"    - {error}")
        else:
            print(f"  ✅ Turno válido")

def generar_reporte(resultados):
    """
    Generar reporte de resultados
    """
    print("\n\n📊 REPORTE DE RESULTADOS")
    print("=" * 50)
    
    total = len(resultados)
    validos = sum(1 for r in resultados if r['valido'])
    invalidos = total - validos
    
    print(f"Total de pruebas: {total}")
    print(f"✅ Válidos: {validos}")
    print(f"❌ Inválidos: {invalidos}")
    print(f"📈 Tasa de éxito: {(validos/total)*100:.1f}%")
    
    print("\n📝 Detalles:")
    for resultado in resultados:
        estado = "✅" if resultado['valido'] else "❌"
        print(f"{estado} {resultado['entrada']} → {resultado['resultado']} ({resultado['descripcion']})")

def main():
    """
    Función principal
    """
    print("🚀 INICIANDO PRUEBAS DE FORMATO MILITAR")
    print("=" * 60)
    
    # Probar validaciones individuales
    resultados = probar_validaciones()
    
    # Probar segmentos completos
    probar_segmentos()
    
    # Generar reporte
    generar_reporte(resultados)
    
    print("\n\n🎯 RECOMENDACIONES:")
    print("=" * 50)
    print("1. ✅ Usar siempre formato HH:MM (00:00 a 23:59)")
    print("2. ✅ Validar entrada en frontend y backend")
    print("3. ✅ Convertir automáticamente formato 12h a 24h")
    print("4. ✅ Usar regex específico para validación militar")
    print("5. ✅ Mantener consistencia en toda la aplicación")
    
    print("\n✅ Pruebas completadas")

if __name__ == "__main__":
    main() 
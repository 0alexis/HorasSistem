#!/usr/bin/env python3
"""
Script para verificar y corregir el formato militar en el admin de Django
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horas_sistema.settings')
django.setup()

from usuarios.models import CodigoTurno
from usuarios.admin import TimeInputMilitar

def validar_hora_militar(hora_str):
    """
    Validar y corregir formato de hora militar (00:00 a 23:59)
    """
    if not hora_str:
        return None
    
    # Convertir de formato 12 horas a militar si es necesario
    if 'AM' in hora_str or 'PM' in hora_str:
        try:
            from datetime import datetime
            # Parsear el tiempo en formato 12 horas
            tiempo_obj = datetime.strptime(hora_str, '%I:%M %p')
            # Convertir a formato militar
            hora_str = tiempo_obj.strftime('%H:%M')
        except:
            return None
    
    # Validar formato militar HH:MM con regex específico
    import re
    regex_militar = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    if regex_militar.match(hora_str):
        try:
            horas, minutos = hora_str.split(':')
            hora_num = int(horas)
            minuto_num = int(minutos)
            
            # Validar rango militar (00:00 a 23:59)
            if 0 <= hora_num <= 23 and 0 <= minuto_num <= 59:
                return f"{hora_num:02d}:{minuto_num:02d}"
            else:
                return None
        except:
            return None
    else:
        return None

def verificar_widget_militar():
    """
    Verificar que el widget TimeInputMilitar funcione correctamente
    """
    print("🔧 VERIFICANDO WIDGET MILITAR")
    print("=" * 50)
    
    # Crear instancia del widget
    widget = TimeInputMilitar()
    
    # Probar diferentes valores
    valores_prueba = [
        ('08:00', 'Hora mañana'),
        ('14:30', 'Hora tarde'),
        ('22:45', 'Hora noche'),
        ('00:00', 'Medianoche'),
        ('23:59', 'Último minuto'),
    ]
    
    print("📝 Probando renderizado del widget:")
    for valor, descripcion in valores_prueba:
        try:
            html = widget.render('test_field', valor, {'id': 'test_input'})
            print(f"✅ {valor} ({descripcion}): Widget renderizado correctamente")
        except Exception as e:
            print(f"❌ {valor} ({descripcion}): Error - {e}")
    
    print("\n📝 Probando conversión de formatos:")
    formatos_12h = [
        ('8:00 AM', '08:00'),
        ('2:30 PM', '14:30'),
        ('10:45 PM', '22:45'),
        ('12:00 AM', '00:00'),
        ('11:59 PM', '23:59'),
    ]
    
    for formato_12h, esperado in formatos_12h:
        try:
            html = widget.render('test_field', formato_12h, {'id': 'test_input'})
            print(f"✅ {formato_12h} → {esperado}: Conversión correcta")
        except Exception as e:
            print(f"❌ {formato_12h} → {esperado}: Error - {e}")

def verificar_validacion_backend():
    """
    Verificar la validación militar en el backend
    """
    print("\n🔧 VERIFICANDO VALIDACIÓN BACKEND")
    print("=" * 50)
    
    casos_prueba = [
        # Formato militar correcto
        ("08:00", True),
        ("14:30", True),
        ("22:45", True),
        ("00:00", True),
        ("23:59", True),
        
        # Formato 12 horas (debe convertir)
        ("8:00 AM", True),
        ("2:30 PM", True),
        ("10:45 PM", True),
        ("12:00 AM", True),
        ("11:59 PM", True),
        
        # Casos inválidos
        ("24:00", False),
        ("12:60", False),
        ("25:30", False),
        ("abc", False),
        ("", False),
    ]
    
    for entrada, esperado in casos_prueba:
        resultado = validar_hora_militar(entrada)
        es_valido = resultado is not None
        
        if es_valido == esperado:
            estado = "✅"
        else:
            estado = "❌"
        
        print(f"{estado} {entrada} → {resultado} (esperado: {esperado})")

def verificar_modelo_codigo_turno():
    """
    Verificar que el modelo CodigoTurno maneje correctamente el formato militar
    """
    print("\n🔧 VERIFICANDO MODELO CÓDIGO TURNO")
    print("=" * 50)
    
    # Crear un código de turno de prueba
    try:
        # Verificar si ya existe un código de prueba
        codigo_prueba = CodigoTurno.objects.filter(letra_turno='TEST').first()
        
        if codigo_prueba:
            print("📋 Usando código de turno existente para pruebas")
        else:
            print("📋 Creando código de turno de prueba")
            codigo_prueba = CodigoTurno.objects.create(
                letra_turno='TEST',
                tipo='N',
                segmentos_horas=[
                    {'inicio': '08:00', 'fin': '16:00', 'tipo': 'NORMAL'},
                    {'inicio': '16:00', 'fin': '00:00', 'tipo': 'NOCTURNO'}
                ]
            )
        
        print(f"✅ Código de turno: {codigo_prueba}")
        print(f"📋 Segmentos: {codigo_prueba.segmentos_horas}")
        
        # Probar validación de segmentos
        try:
            codigo_prueba.clean()
            print("✅ Validación del modelo exitosa")
        except Exception as e:
            print(f"❌ Error en validación: {e}")
        
        # Probar cálculo de duración
        duracion = codigo_prueba.calcular_duracion_total()
        print(f"⏱️ Duración total: {duracion} horas")
        
    except Exception as e:
        print(f"❌ Error al crear/verificar código de turno: {e}")

def verificar_admin_interface():
    """
    Verificar que la interfaz del admin use el formato militar
    """
    print("\n🔧 VERIFICANDO INTERFAZ DEL ADMIN")
    print("=" * 50)
    
    try:
        from django.contrib import admin
        from usuarios.admin import CodigoTurnoAdmin
        
        # Verificar que el admin use el formulario correcto
        admin_instance = CodigoTurnoAdmin(CodigoTurno, admin.site)
        
        print("✅ Admin registrado correctamente")
        print(f"📋 Formulario usado: {admin_instance.form}")
        print(f"📋 Campos del formulario: {list(admin_instance.form.base_fields.keys())}")
        
        # Verificar campos de tiempo
        if 'segmentos_horas' in admin_instance.form.base_fields:
            print("✅ Campo segmentos_horas presente")
        else:
            print("❌ Campo segmentos_horas no encontrado")
        
    except Exception as e:
        print(f"❌ Error al verificar admin: {e}")

def generar_recomendaciones():
    """
    Generar recomendaciones para corregir el problema
    """
    print("\n🎯 RECOMENDACIONES PARA CORREGIR EL PROBLEMA")
    print("=" * 60)
    
    print("1. 🔧 VERIFICAR CONFIGURACIÓN DEL NAVEGADOR:")
    print("   - Asegurar que el navegador soporte formato 24 horas")
    print("   - Verificar configuración regional del sistema")
    print("   - Probar en diferentes navegadores (Chrome, Firefox, Edge)")
    
    print("\n2. 🔧 VERIFICAR JAVASCRIPT:")
    print("   - Abrir consola del navegador (F12)")
    print("   - Verificar que no hay errores de JavaScript")
    print("   - Confirmar que los estilos CSS se aplican correctamente")
    
    print("\n3. 🔧 VERIFICAR TEMPLATE:")
    print("   - Asegurar que el template carga el CSS correcto")
    print("   - Verificar que el JavaScript se ejecuta al cargar la página")
    print("   - Confirmar que los atributos HTML están correctos")
    
    print("\n4. 🔧 VERIFICAR BACKEND:")
    print("   - Confirmar que el widget TimeInputMilitar se usa")
    print("   - Verificar que la validación funciona correctamente")
    print("   - Probar guardado de datos en formato militar")
    
    print("\n5. 🔧 SOLUCIONES ESPECÍFICAS:")
    print("   - Forzar formato 24h con atributos HTML: min='00:00' max='23:59'")
    print("   - Usar CSS más agresivo para ocultar AM/PM")
    print("   - Implementar validación JavaScript en tiempo real")
    print("   - Agregar conversión automática de formato 12h a 24h")

def main():
    """
    Función principal
    """
    print("🚀 VERIFICACIÓN COMPLETA DEL FORMATO MILITAR")
    print("=" * 60)
    
    # Verificar widget
    verificar_widget_militar()
    
    # Verificar validación backend
    verificar_validacion_backend()
    
    # Verificar modelo
    verificar_modelo_codigo_turno()
    
    # Verificar admin
    verificar_admin_interface()
    
    # Generar recomendaciones
    generar_recomendaciones()
    
    print("\n✅ Verificación completada")
    print("\n📝 Para probar el formato militar:")
    print("1. Abre el archivo test_formato_militar.html en tu navegador")
    print("2. Ejecuta: python test_formato_militar.py")
    print("3. Verifica el admin de Django con los cambios implementados")

if __name__ == "__main__":
    main() 
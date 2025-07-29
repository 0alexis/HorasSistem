"""
utils.py

Este archivo contiene funciones y clases utilitarias para la programación automática de turnos.
Permite asignar turnos a empleados según diferentes patrones definidos en los modelos de turno,
facilitando la extensión a nuevos tipos de patrones y centralizando la lógica de asignación.

Componentes principales:
- Función para obtener el patrón de turnos desde la base de datos.
- Generadores de turnos para distintos tipos de patrones (ej: 16D, 6D, etc.).
- Clase principal para programar turnos usando el generador adecuado.
- Función utilitaria para crear las asignaciones de turnos en la base de datos.
"""
from datetime import timedelta
from .models import AsignacionTurno
from django.contrib.auth.models import User
from .models import Bitacora
import threading
from django.utils.deprecation import MiddlewareMixin

# Variable global para almacenar valores anteriores
_valores_anteriores = {}

_request_local = threading.local()

def obtener_patron(modelo_turno):
    # Devuelve una matriz de letras (lista de listas) desde la base de datos
    letras = modelo_turno.letras.order_by('fila', 'columna')
    filas = {}
    for l in letras:
        filas.setdefault(l.fila, []).append(l.valor)
    return [filas[k] for k in sorted(filas.keys())]

class Generador16D:
    def generar(self, empleados, semanas, patron):
        horarios = []
        dia_patron = 0
        total_patrones = len(patron)
        bloques_completos = len(empleados) // total_patrones
        sobrantes = empleados[bloques_completos * total_patrones:]
        empleados_base = empleados[:bloques_completos * total_patrones]

        for semana in range(semanas):
            for i, emp in enumerate(empleados_base):
                patron_fila = patron[i % total_patrones]
                for dia in range(7):
                    idx = (dia_patron + dia) % len(patron_fila)
                    fecha = semana * 7 + dia  # O usa fecha_inicio + timedelta
                    horarios.append({
                        'empleado_id': emp.id,
                        'semana': semana,
                        'dia': dia,
                        'turno': patron_fila[idx]
                    })
            for i, emp in enumerate(sobrantes):
                patron_fila = patron[i % total_patrones]
                for dia in range(7):
                    idx = (dia_patron + dia) % len(patron_fila)
                    fecha = semana * 7 + dia
                    horarios.append({
                        'empleado_id': emp.id,
                        'semana': semana,
                        'dia': dia,
                        'turno': patron_fila[idx]
                    })
            dia_patron = (dia_patron + 7) % len(patron[0])
        return horarios

# ... (puedes adaptar Generador6D y Generador18D_H igual)
#pendiente adaptar las demas generadores

class ProgramadorTurnos:
    def __init__(self):
        self.generadores = {
            '16D': Generador16D(),
            # '6D': Generador6D(),
            # '18H': Generador18D_H(),
        }

    def programar(self, modelo_turno, empleados, semanas):
        patron = obtener_patron(modelo_turno)
        gen = self.generadores.get(modelo_turno.tipo_codigo)  # tipo_codigo: '16D', '6D', etc.
        if not gen:
            raise ValueError(f"Modelo de turno '{modelo_turno.tipo_codigo}' no soportado")
        return gen.generar(empleados, semanas, patron)

def programar_turnos(modelo_turno, empleados, fecha_inicio, fecha_fin, programacion):
    # Obtener el centro operativo desde la instancia de programacion
    centro_operativo = programacion.centro_operativo if hasattr(programacion, 'centro_operativo') else None
    pv = getattr(centro_operativo, 'promesa_valor', None)
    tipo = getattr(modelo_turno, 'tipo', None)
#calculo para promesa de valor cuando el modelo es fijo
    if tipo == 'F' and pv is not None:
        min_personas = pv * 4 #valor predetermiando para puntos fijos
        if len(empleados) < min_personas:
            raise ValueError(f"Para modelos de tipo FIJO se requieren al menos {min_personas} personas para realizar esta programacion. Solo hay {len(empleados)} empleados disponibles.")
   
   
    # Dejar la puerta abierta para lógica futura en modelos variables
    elif tipo == 'V':
        # TODO: Implementar lógica de validación para modelos variables cuando esté definida
        pass
#################################################################
    letras = modelo_turno.letras.order_by('fila', 'columna')
    
    filas = {}
    for l in letras:
        filas.setdefault(l.fila, []).append(l.valor)
    filas_ordenadas = [filas[k] for k in sorted(filas.keys())]
    dias = (fecha_fin - fecha_inicio).days + 1

    for idx, empleado in enumerate(empleados):
        fila_idx = idx % len(filas_ordenadas)
        fila = filas_ordenadas[fila_idx]
        for dia_offset in range(dias):
            fecha = fecha_inicio + timedelta(days=dia_offset)
            letra = fila[dia_offset % len(fila)]
            columna = dia_offset % len(fila)  #  cálculo correcto según tu lógica
            AsignacionTurno.objects.create(
                programacion=programacion,
                tercero=empleado,
                dia=fecha,
                letra_turno=letra,
                fila=fila_idx,
                columna=columna
            )

def get_client_ip(request):
    """Obtiene la IP del cliente desde el request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def registrar_bitacora(request, tipo_accion, modulo, modelo_afectado, objeto_id=None, 
                      descripcion="", valores_anteriores=None, valores_nuevos=None, 
                      campos_modificados=None):
    """
    Registra una acción en la bitácora
    
    Args:
        request: Request de Django
        tipo_accion: CREAR, EDITAR, ELIMINAR, CONSULTAR
        modulo: programacion, turnos, empleados, modelos, usuarios
        modelo_afectado: Nombre del modelo (ej: 'ProgramacionHorario')
        objeto_id: ID del objeto afectado
        descripcion: Descripción de la acción
        valores_anteriores: Dict con valores anteriores (para ediciones)
        valores_nuevos: Dict con valores nuevos
        campos_modificados: Lista de campos modificados
    """
    print(f"📝 Intentando registrar bitácora: {tipo_accion} - {modulo} - {modelo_afectado}")
    
    try:
        usuario = request.user if request and hasattr(request, 'user') else None
        ip_address = get_client_ip(request) if request else '127.0.0.1'  # IP por defecto
        
        print(f"👤 Usuario: {usuario}")
        print(f"🌐 IP: {ip_address}")
        
        bitacora = Bitacora.objects.create(
            usuario=usuario,
            ip_address=ip_address,
            tipo_accion=tipo_accion,
            modulo=modulo,
            modelo_afectado=modelo_afectado,
            objeto_id=objeto_id,
            descripcion=descripcion,
            valores_anteriores=valores_anteriores,
            valores_nuevos=valores_nuevos,
            campos_modificados=campos_modificados
        )
        
        print(f"✅ Bitácora registrada exitosamente: ID {bitacora.id}")
        return bitacora
        
    except Exception as e:
        # Log del error pero no interrumpir el flujo principal
        print(f"❌ Error al registrar bitácora: {e}")
        import traceback
        traceback.print_exc()
        return None

def obtener_valores_anteriores(instance, fields_to_track=None):
    """
    Obtiene los valores anteriores de un objeto para comparación
    
    Args:
        instance: Instancia del modelo
        fields_to_track: Lista de campos a rastrear (si None, usa todos)
    
    Returns:
        Dict con los valores anteriores
    """
    if not instance.pk:  # Objeto nuevo, no hay valores anteriores
        return {}
    
    try:
        # Obtener el objeto de la base de datos
        old_instance = instance.__class__.objects.get(pk=instance.pk)
        valores = {}
        
        if fields_to_track:
            campos = fields_to_track
        else:
            # Obtener todos los campos del modelo
            campos = [field.name for field in instance._meta.fields 
                     if not field.primary_key and not field.auto_created]
        
        for campo in campos:
            if hasattr(old_instance, campo):
                valor = getattr(old_instance, campo)
                # Convertir a string para JSON
                if hasattr(valor, '__str__'):
                    valores[campo] = str(valor)
                else:
                    valores[campo] = valor
        
        return valores
    except instance.__class__.DoesNotExist:
        return {}
    except Exception as e:
        print(f"Error al obtener valores anteriores: {e}")
        return {}

def comparar_valores(valores_anteriores, valores_nuevos):
    """
    Compara valores anteriores y nuevos para encontrar cambios
    
    Returns:
        Lista de campos modificados
    """
    campos_modificados = []
    
    for campo, valor_nuevo in valores_nuevos.items():
        valor_anterior = valores_anteriores.get(campo)
        if valor_anterior != valor_nuevo:
            campos_modificados.append(campo)
    
    return campos_modificados

def registrar_bitacora_automatica(sender, instance, created, **kwargs):
    """
    Función automática para registrar bitácora en cualquier modelo
    """
    try:
        # Evitar recursión infinita - no registrar cambios en la bitácora misma
        if sender._meta.model_name == 'bitacora':
            return
            
        from .middleware import get_current_request
        request = get_current_request()
        
        # Determinar el módulo basado en el nombre de la app
        app_label = sender._meta.app_label
        modulo_map = {
            'programacion_turnos': 'programacion',
            'usuarios': 'usuarios',
            'empresas': 'empresas',
            'programacion_models': 'modelos',
        }
        modulo = modulo_map.get(app_label, app_label)
        
        # Determinar tipo de acción
        tipo_accion = 'CREAR' if created else 'EDITAR'
        
        # Obtener valores del modelo
        valores = {}
        for field in instance._meta.fields:
            if not field.primary_key and not field.auto_created:
                try:
                    value = getattr(instance, field.name)
                    if hasattr(value, '__str__'):
                        valores[field.name] = str(value)
                    else:
                        valores[field.name] = value
                except:
                    valores[field.name] = None
        
        # Crear descripción
        if hasattr(instance, '__str__'):
            descripcion = f"{sender._meta.verbose_name} {tipo_accion.lower()}: {instance}"
        else:
            descripcion = f"{sender._meta.verbose_name} {tipo_accion.lower()}: ID {instance.pk}"
        
        # Para ediciones, comparar con valores anteriores
        valores_anteriores = None
        campos_modificados = None
        
        if not created:
            valores_anteriores = _valores_anteriores.get(instance.pk, {})
            campos_modificados = comparar_valores(valores_anteriores, valores)
            
            # Solo registrar si hay cambios
            if not campos_modificados:
                return
        
        registrar_bitacora(
            request=request,
            tipo_accion=tipo_accion,
            modulo=modulo,
            modelo_afectado=sender._meta.model_name,
            objeto_id=instance.pk,
            descripcion=descripcion,
            valores_anteriores=valores_anteriores,
            valores_nuevos=valores,
            campos_modificados=campos_modificados
        )
        
    except Exception as e:
        print(f"❌ Error en bitácora automática para {sender._meta.model_name}: {e}")

def registrar_eliminacion_automatica(sender, instance, **kwargs):
    """
    Función automática para registrar eliminaciones en cualquier modelo
    """
    try:
        # Evitar recursión infinita - no registrar eliminaciones de la bitácora misma
        if sender._meta.model_name == 'bitacora':
            return
            
        from .middleware import get_current_request
        request = get_current_request()
        
        # Determinar el módulo basado en el nombre de la app
        app_label = sender._meta.app_label
        modulo_map = {
            'programacion_turnos': 'programacion',
            'usuarios': 'usuarios',
            'empresas': 'empresas',
            'programacion_models': 'modelos',
        }
        modulo = modulo_map.get(app_label, app_label)
        
        # Obtener valores del modelo
        valores = {}
        for field in instance._meta.fields:
            if not field.primary_key and not field.auto_created:
                try:
                    value = getattr(instance, field.name)
                    if hasattr(value, '__str__'):
                        valores[field.name] = str(value)
                    else:
                        valores[field.name] = value
                except:
                    valores[field.name] = None
        
        # Crear descripción
        if hasattr(instance, '__str__'):
            descripcion = f"{sender._meta.verbose_name} eliminado: {instance}"
        else:
            descripcion = f"{sender._meta.verbose_name} eliminado: ID {instance.pk}"
        
        registrar_bitacora(
            request=request,
            tipo_accion='ELIMINAR',
            modulo=modulo,
            modelo_afectado=sender._meta.model_name,
            objeto_id=instance.pk,
            descripcion=descripcion,
            valores_anteriores=valores
        )
        
    except Exception as e:
        print(f"❌ Error en bitácora automática de eliminación para {sender._meta.model_name}: {e}")

def capturar_valores_anteriores_automatico(sender, instance, **kwargs):
    """
    Función automática para capturar valores anteriores antes de guardar
    """
    if instance.pk:  # Solo para objetos existentes
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            valores = {}
            for field in instance._meta.fields:
                if not field.primary_key and not field.auto_created:
                    try:
                        value = getattr(old_instance, field.name)
                        if hasattr(value, '__str__'):
                            valores[field.name] = str(value)
                        else:
                            valores[field.name] = value
                    except:
                        valores[field.name] = None
            _valores_anteriores[instance.pk] = valores
        except sender.DoesNotExist:
            pass
        except Exception as e:
            print(f"❌ Error capturando valores anteriores para {sender._meta.model_name}: {e}")

def registrar_modelo_automaticamente(model_class):
    """
    Decorador para registrar automáticamente un modelo en la bitácora
    """
    from django.db.models.signals import post_save, post_delete, pre_save
    
    # Registrar signals automáticamente
    post_save.connect(registrar_bitacora_automatica, sender=model_class)
    post_delete.connect(registrar_eliminacion_automatica, sender=model_class)
    pre_save.connect(capturar_valores_anteriores_automatico, sender=model_class)
    
    return model_class

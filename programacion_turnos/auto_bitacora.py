"""
Sistema de bitácora automática para todos los modelos del sistema
"""
from django.apps import apps
from django.db.models.signals import post_save, post_delete, pre_save
from .utils import (
    registrar_bitacora_automatica, 
    registrar_eliminacion_automatica, 
    capturar_valores_anteriores_automatico
)

def registrar_todos_los_modelos():
    """
    Registra automáticamente todos los modelos del sistema en la bitácora
    """
    # Obtener todas las apps instaladas
    installed_apps = apps.get_app_configs()
    
    # Apps que queremos rastrear
    apps_a_rastrear = [
        'programacion_turnos',
        'usuarios', 
        'empresas',
        'programacion_models'
    ]
    
    modelos_registrados = []
    
    for app_config in installed_apps:
        if app_config.label in apps_a_rastrear:
            
            for model in app_config.get_models():
                # Excluir modelos del sistema Django
                if model._meta.app_label in apps_a_rastrear:
                    try:
                        # Registrar signals para el modelo
                        post_save.connect(registrar_bitacora_automatica, sender=model)
                        post_delete.connect(registrar_eliminacion_automatica, sender=model)
                        pre_save.connect(capturar_valores_anteriores_automatico, sender=model)
                        
                        modelos_registrados.append(f"{model._meta.app_label}.{model._meta.model_name}")
                        
                    except Exception as e:
                        pass

    return modelos_registrados

def registrar_modelo_especifico(model_class):
    """
    Registra un modelo específico en la bitácora
    """
    try:
        post_save.connect(registrar_bitacora_automatica, sender=model_class)
        post_delete.connect(registrar_eliminacion_automatica, sender=model_class)
        pre_save.connect(capturar_valores_anteriores_automatico, sender=model_class)
        
        return True
        
    except Exception as e:
        return False

def obtener_modelos_rastreados():
    """
    Retorna una lista de todos los modelos que están siendo rastreados
    """
    modelos = []
    installed_apps = apps.get_app_configs()
    
    apps_a_rastrear = [
        'programacion_turnos',
        'usuarios', 
        'empresas',
        'programacion_models'
    ]
    
    for app_config in installed_apps:
        if app_config.label in apps_a_rastrear:
            for model in app_config.get_models():
                if model._meta.app_label in apps_a_rastrear:
                    modelos.append({
                        'app': model._meta.app_label,
                        'modelo': model._meta.model_name,
                        'verbose_name': model._meta.verbose_name
                    })
    
    return modelos 
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Bitacora
from .utils import _valores_anteriores
from .auto_bitacora import registrar_todos_los_modelos

# Registrar automáticamente todos los modelos del sistema
print("🚀 Iniciando registro automático de bitácora...")
modelos_registrados = registrar_todos_los_modelos()
print(f"✅ Sistema de bitácora automática activado para {len(modelos_registrados)} modelos") 
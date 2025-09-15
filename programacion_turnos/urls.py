from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    ProgramacionHorarioViewSet, 
    AsignacionTurnoViewSet, 
    asignacion_turno_modulo, 
    centros_por_proyecto_view, 
    dashboard_view, 
    malla_turnos, 
    editar_malla_api, 
    intercambiar_terceros_api, 
    nomina_view,
    test_bitacora, 
    HolidayJsView, 
    programaciones_por_centro_view,
    crear_programacion_view, 
    editar_letra_turno_api,
    asignacion_turno_edit_view,
    bitacora_dashboard
)

# ========== ROUTER PARA APIs DRF ==========
router = DefaultRouter()
router.register(r'programacion', ProgramacionHorarioViewSet, basename='programacion')
router.register(r'asignacionturno', AsignacionTurnoViewSet, basename='asignacionturno')

# ========== TODAS LAS RUTAS (MANTENER IGUAL) ==========
urlpatterns = [
    # Dashboard principal
    path('programacionhorario/', dashboard_view, name='programacion_dashboard'),
    path('proyecto/<int:proyecto_id>/centros/', centros_por_proyecto_view, name='centros_por_proyecto'),
    
    # Vistas de programación
    path('malla/<int:programacion_id>/', malla_turnos, name='malla_turnos'),
    path('programacionhorario/centro/<int:centro_id>/', programaciones_por_centro_view, name='programaciones_por_centro'),
    path('programacionhorario/crear/<int:centro_id>/', crear_programacion_view, name='crear_programacion_centro'),
    
    # Módulos de asignación
    path('asignacionturno/', asignacion_turno_modulo, name='asignacion_turno_modulo'),
    path('asignacionturno/<str:llave>/change/', asignacion_turno_edit_view, name='asignacion_turno_edit'),
    
    # Vistas de nomina (✅ MANTENER - se usa en API)
    path('nomina/<int:programacion_id>/', nomina_view, name='nomina_view'),

    # APIs del router DRF (✅ MANTENER)
    path('', include(router.urls)),
    
    # APIs específicas (✅ MANTENER)
    path('programacion/<int:programacion_id>/editar_malla/', editar_malla_api, name='editar_malla_api'),
    path('programacion/<int:programacion_id>/intercambiar_terceros/', intercambiar_terceros_api, name='intercambiar_terceros_api'),
    path('editar-letra-turno/', editar_letra_turno_api, name='editar_letra_turno_api'),
    
    # Archivos JS dinámicos (✅ MANTENER)
    path('js/holidays.js', HolidayJsView.as_view(), name='holidays_js'),
    
    # Test (✅ MANTENER)
    path('test-bitacora/', test_bitacora, name='test_bitacora'),
]

# ========== RUTAS SOLO PARA WEB (NO API) ==========
web_only_patterns = [
    # ✅ BITÁCORA - SOLO DISPONIBLE EN /programacion_turnos/
    path('bitacora/', bitacora_dashboard, name='bitacora_dashboard'),
]

# ✅ CONCATENAR: todas las rutas + solo las de web
urlpatterns = urlpatterns + web_only_patterns

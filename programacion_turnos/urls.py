from rest_framework.routers import DefaultRouter
from .views import (ProgramacionHorarioViewSet, 
    AsignacionTurnoViewSet, asignacion_turno_modulo, centros_por_proyecto_view, dashboard_view, 
    malla_turnos, editar_malla_api, intercambiar_terceros_api, nomina_view,
    test_bitacora, HolidayJsView, 
    programaciones_por_centro_view,
    crear_programacion_view, editar_letra_turno_api,
    asignacion_turno_edit_view)
from django.urls import path, include

# ========== ROUTER PARA APIs DRF ==========
router = DefaultRouter()
router.register(r'programacion', ProgramacionHorarioViewSet, basename='programacion')
router.register(r'asignacionturno', AsignacionTurnoViewSet, basename='asignacionturno')

# ========== RUTAS HTML (VISTAS CON TEMPLATES) ==========
html_urlpatterns = [
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
    
    # Vistas de nomina
    path('nomina/<int:programacion_id>/', nomina_view, name='nomina_view'),

    # Test y utilidades
    path('test-bitacora/', test_bitacora, name='test_bitacora'),
]

# ========== RUTAS API (JSON/AJAX) ==========
api_urlpatterns = [
    # APIs del router DRF
    path('', include(router.urls)),
    
    # APIs específicas
    path('programacion/<int:programacion_id>/editar_malla/', editar_malla_api, name='editar_malla_api'),
    path('programacion/<int:programacion_id>/intercambiar_terceros/', intercambiar_terceros_api, name='intercambiar_terceros_api'),
    path('api/editar-letra-turno/', editar_letra_turno_api, name='editar_letra_turno_api'),
    
    # Archivos JS dinámicos
    path('js/holidays.js', HolidayJsView.as_view(), name='holidays_js'),
]

# ========== TODAS LAS RUTAS (MANTIENE COMPORTAMIENTO ACTUAL) ==========
urlpatterns = html_urlpatterns + api_urlpatterns

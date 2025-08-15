from rest_framework.routers import DefaultRouter
from .views import (ProgramacionHorarioViewSet, 
    AsignacionTurnoViewSet, dashboard_view, 
    malla_turnos, editar_malla_api, intercambiar_terceros_api,
    test_bitacora, HolidayJsView, 
    programaciones_por_centro_view,
    crear_programacion_view)
from django.urls import path, include

router = DefaultRouter()
router.register(r'programacion', ProgramacionHorarioViewSet, basename='programacion')
router.register(r'asignacionturno', AsignacionTurnoViewSet, basename='asignacionturno')

urlpatterns = [
    # Cambia 'dashboard/' por 'programacionhorario/'
    path('programacionhorario/', dashboard_view, name='programacion_dashboard'),
    path('', include(router.urls)),
    path('malla/<int:programacion_id>/', malla_turnos, name='malla_turnos'),
    path('programacion/<int:programacion_id>/editar_malla/', editar_malla_api, name='editar_malla_api'),
    path('programacion/<int:programacion_id>/intercambiar_terceros/', intercambiar_terceros_api, name='intercambiar_terceros_api'),
    path('test-bitacora/', test_bitacora, name='test_bitacora'),
    path('js/holidays.js', HolidayJsView.as_view(), name='holidays_js'),

    path('programacionhorario/centro/<int:centro_id>/', programaciones_por_centro_view, name='programaciones_por_centro'),
    path('programacionhorario/crear/<int:centro_id>/', crear_programacion_view, name='crear_programacion_centro'),

    

]

#urlpatterns += [
#    
#]

from rest_framework.routers import DefaultRouter
from .views import ProgramacionHorarioViewSet, AsignacionTurnoViewSet, malla_turnos, editar_malla_api, intercambiar_terceros_api
from django.urls import path, include

router = DefaultRouter()
router.register(r'programacion', ProgramacionHorarioViewSet, basename='programacion')
router.register(r'asignacionturno', AsignacionTurnoViewSet, basename='asignacionturno')

urlpatterns = [
    path('', include(router.urls)),
    path('malla/<int:programacion_id>/', malla_turnos, name='malla_turnos'),
    path('programacion/<int:programacion_id>/editar_malla/', editar_malla_api, name='editar_malla_api'),
    path('programacion/<int:programacion_id>/intercambiar_terceros/', intercambiar_terceros_api, name='intercambiar_terceros_api'),
]

#urlpatterns += [
#    
#]

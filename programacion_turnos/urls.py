from rest_framework.routers import DefaultRouter
from .views import ProgramacionHorarioViewSet, AsignacionTurnoViewSet, malla_turnos
from django.urls import path, include

router = DefaultRouter()
router.register(r'programacion', ProgramacionHorarioViewSet, basename='programacion')
router.register(r'asignacionturno', AsignacionTurnoViewSet, basename='asignacionturno')

urlpatterns = [
    path('', include(router.urls)),
    path('malla/<int:programacion_id>/', malla_turnos, name='malla_turnos'),
]
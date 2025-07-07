from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModeloTurnoViewSet

app_name = 'programacion_models'

router = DefaultRouter()
router.register(r'modeloturno', ModeloTurnoViewSet, basename='modeloturno')

urlpatterns = [
    path('', include(router.urls)),
]
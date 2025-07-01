from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatronBaseListView, PatronBaseDetailView,  # HTML
    PatronBaseListAPI, PatronBaseDetailAPI,    # API REST
    ModeloTurnoViewSet                        # API REST
)

app_name = 'programacion_models'

router = DefaultRouter()
router.register(r'modeloturno', ModeloTurnoViewSet, basename='modeloturno')

urlpatterns = [
    # Vistas HTML
    path('patrones/html/', PatronBaseListView.as_view(), name='patronbase-list-html'),
    path('patrones/html/<int:pk>/', PatronBaseDetailView.as_view(), name='patronbase-detail-html'),

    # Vistas API REST
    path('patrones/', PatronBaseListAPI.as_view(), name='patronbase-list'),
    path('patrones/<int:pk>/', PatronBaseDetailAPI.as_view(), name='patronbase-detail'),

    # Endpoints API REST para ModeloTurno
    path('', include(router.urls)),
]
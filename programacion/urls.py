from django.urls import path
from .views import ModeloTurnoListView, ModeloTurnoDetailView

app_name = 'programacion'  # Cambiado de 'programacion_models' a 'programacion'

urlpatterns = [
    # View for listing all models
    path('modelos/', ModeloTurnoListView.as_view(), name='modelo_list'),
    
    # View for model details
    path('modelos/<int:pk>/', ModeloTurnoDetailView.as_view(), name='modelo_detail'),
]
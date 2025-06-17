from django.urls import path
from .views import ModeloTurnoListView, ModeloTurnoDetailView

app_name = 'programacion_models'

urlpatterns = [
    path('', ModeloTurnoListView.as_view(), name='modelo_list'),
    path('<int:pk>/', ModeloTurnoDetailView.as_view(), name='modelo_detail'),
]
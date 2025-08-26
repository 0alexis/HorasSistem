from django.urls import path
from . import views

app_name = 'programacion_models'

urlpatterns = [
    path('modeloturno/nuevo/', views.modeloturno_create, name='modeloturno_create'),
    path('modeloturno/<int:pk>/editar/', views.modeloturno_update, name='modeloturno_update'),
    path('modeloturno/', views.modeloturno_list, name='modeloturno_list'),  # Si tienes una vista de listado
    path('modeloturno/<int:pk>/', views.modeloturno_detail, name='modeloturno_detail'),
]
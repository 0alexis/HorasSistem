from django.urls import path
from .views import PatronBaseListView, PatronBaseDetailView

app_name = 'programacion_models'

urlpatterns = [
    path('patrones/', PatronBaseListView.as_view(), name='patronbase-list'),
    path('patrones/<int:pk>/', PatronBaseDetailView.as_view(), name='patronbase-detail'),
]
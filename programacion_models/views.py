from django.views.generic import ListView, DetailView
from rest_framework import generics, viewsets
from .models import ModeloTurno
from .serializers import ModeloTurnoSerializer

class ModeloTurnoViewSet(viewsets.ModelViewSet):
    queryset = ModeloTurno.objects.all()
    serializer_class = ModeloTurnoSerializer

# Si en el futuro necesitas vistas personalizadas para ModeloTurno,
# puedes importarlo así:
# from .models import ModeloTurno
#recuerda que el querer es poder
# Por ahora, si solo usas el admin, este archivo puede quedar vacío.

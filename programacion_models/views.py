from django.views.generic import ListView, DetailView
from .patrones_base.patrones_base import PatronBase
from rest_framework import generics, viewsets
from .serializers import PatronBaseSerializer, ModeloTurnoSerializer
from .models import ModeloTurno

class PatronBaseListView(ListView):
    model = PatronBase
    template_name = 'patronbase_list.html'  # Debes crear este template

class PatronBaseDetailView(DetailView):
    model = PatronBase
    template_name = 'patronbase_detail.html'  # Debes crear este template

class PatronBaseListAPI(generics.ListCreateAPIView):
    queryset = PatronBase.objects.all()
    serializer_class = PatronBaseSerializer

class PatronBaseDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = PatronBase.objects.all()
    serializer_class = PatronBaseSerializer

class ModeloTurnoViewSet(viewsets.ModelViewSet):
    queryset = ModeloTurno.objects.all()
    serializer_class = ModeloTurnoSerializer

# Si en el futuro necesitas vistas personalizadas para ModeloTurno,
# puedes importarlo así:
# from .models import ModeloTurno

# Por ahora, si solo usas el admin, este archivo puede quedar vacío.

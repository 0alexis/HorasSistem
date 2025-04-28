from django.shortcuts import render
from rest_framework import viewsets
from .models import Prueba
from .serializers import PruebaSerializer

# Create your views here.

class PruebaViewSet(viewsets.ModelViewSet):
    queryset = Prueba.objects.all()
    serializer_class = PruebaSerializer

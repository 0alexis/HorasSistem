from rest_framework import serializers
from .patrones_base.patrones_base import PatronBase
from .models import ModeloTurno

class PatronBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatronBase
        fields = '__all__'

class ModeloTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloTurno
        fields = '__all__' 
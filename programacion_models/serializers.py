from rest_framework import serializers
from .models import ModeloTurno, LetraTurno


class LetraTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetraTurno
        fields = '__all__'


class ModeloTurnoSerializer(serializers.ModelSerializer):
    matriz_letras = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = ModeloTurno
        fields = ['id', 'nombre', 'descripcion', 'unidad_negocio', 'tipo', 'matriz_letras']

    def create(self, validated_data):
        letras = validated_data.pop('matriz_letras', [])
        instance = super().create(validated_data)

        # Detecta si el formato es lista de listas o lista de objetos
        if letras and isinstance(letras[0], list):
            # Lista de listas (matriz)
            for fila_idx, fila in enumerate(letras):
                for col_idx, valor in enumerate(fila):
                    if valor:
                        LetraTurno.objects.create(
                            modelo_turno=instance,
                            fila=fila_idx,
                            columna=col_idx,
                            valor=valor
                        )
        elif letras and isinstance(letras[0], dict):
            # Lista de objetos con x (columna), y (fila)
            for letra in letras:
                if letra.get('valor'):
                    LetraTurno.objects.create(
                        modelo_turno=instance,
                        fila=letra['y'],
                        columna=letra['x'],
                        valor=letra['valor']
                    )

        return instance
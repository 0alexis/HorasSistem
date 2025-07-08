from django.db import models
from empresas.models import CentroOperativo, UnidadNegocio

#creacion de modelos en base a los patrones de turnos
TIPO_MODELO = [
    ('F', 'Fijo'),
    ('V', 'Variable'),
]

class ModeloTurno(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    unidad_negocio = models.ForeignKey('empresas.UnidadNegocio', on_delete=models.PROTECT)
    tipo = models.CharField(max_length=1, choices=[('F', 'Fijo'), ('V', 'Variable')], default='F')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
#modelo para las letras de los turnos por coordenas en eje x y 
class LetraTurno(models.Model):
    modelo_turno = models.ForeignKey(ModeloTurno, related_name='letras', on_delete=models.CASCADE)
    fila = models.PositiveIntegerField()
    columna = models.PositiveIntegerField()
    valor = models.CharField(max_length=2)

    class Meta:
        unique_together = ('modelo_turno', 'fila', 'columna')

    def __str__(self):
        return f"{self.valor} ({self.fila}, {self.columna})"


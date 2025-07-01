from django.db import models
from empresas.models import CentroOperativo, UnidadNegocio
from .patrones_base.patrones_base import PatronBase

#creacion de modelos en base a los patrones de turnos
TIPO_MODELO = [
    ('F', 'Fijo'),
    ('V', 'Variable'),
]

class ModeloTurno(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    patron_base = models.ForeignKey(PatronBase, on_delete=models.PROTECT)
    centro_operativo = models.ForeignKey(CentroOperativo, on_delete=models.PROTECT)
    unidad_negocio = models.ForeignKey(UnidadNegocio, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=1, choices=TIPO_MODELO, default='F')
    matriz_letras = models.JSONField(
        blank=True, null=True,
        help_text="Matriz personalizada para este modelo de turno, basada en el patrón base."
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Si no hay matriz personalizada, inicializarla copiando la del patrón base
        if not self.matriz_letras and self.patron_base:
            self.matriz_letras = [fila.copy() for fila in self.patron_base.matriz]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
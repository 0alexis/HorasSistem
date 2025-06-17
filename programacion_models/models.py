from django.db import models
from empresas.models import CentroOperativo, Cargo

class ModeloTurno5x3(models.Model):
    TIPO_TURNO_CHOICES = [
        ('F', 'Fijo'),
        ('V', 'Variable'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    centro_operativo = models.ForeignKey(
        CentroOperativo, 
        on_delete=models.PROTECT,
        related_name='modelos_turno'
    )
    tipo_turno = models.CharField(
        max_length=1,
        choices=TIPO_TURNO_CHOICES,
        default='F',
        help_text='Indica si el modelo es fijo o variable'
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Modelo Turno 5x3'
        verbose_name_plural = 'Modelos Turno 5x3'

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_turno_display()} - {self.centro_operativo}"

class CargoRequerido(models.Model):
    modelo = models.ForeignKey(ModeloTurno5x3, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT)
    cantidad_requerida = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Cargo Requerido'
        verbose_name_plural = 'Cargos Requeridos'
        unique_together = ['modelo', 'cargo']

    def __str__(self):
        return f"{self.cargo} - {self.cantidad_requerida} personas"

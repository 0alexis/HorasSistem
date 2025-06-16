from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from empresas.models import CentroOperativo
from usuarios.models import Tercero, CodigoTurno

class ProgramacionTurnos(models.Model):
    """
    Modelo para gestionar la programación de turnos por centro operativo
    """
    id_programacion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    centro_operativo = models.ForeignKey(
        CentroOperativo,
        on_delete=models.PROTECT,
        related_name='programaciones'
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.IntegerField(
        default=1,
        choices=[
            (0, 'Inactivo'),
            (1, 'Activo'),
            (2, 'En Proceso'),
            (3, 'Finalizado')
        ]
    )
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Programación de Turnos'
        verbose_name_plural = 'Programaciones de Turnos'
        ordering = ['-fecha_inicio']

    def clean(self):
        if self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError({
                'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio'
            })

    def __str__(self):
        return f"{self.nombre} - {self.centro_operativo} ({self.fecha_inicio} al {self.fecha_fin})"

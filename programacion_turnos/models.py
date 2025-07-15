from django.db import models
from programacion_models.models import ModeloTurno, LetraTurno
from usuarios.models import Tercero

# Manager personalizado para soft delete de ProgramacionHorario
class ActivoProgramacionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)

class ProgramacionHorario(models.Model):
    # terceros = models.ManyToManyField('usuarios.Tercero', related_name='programaciones')
    centro_operativo = models.ForeignKey('empresas.CentroOperativo', on_delete=models.CASCADE)
    modelo_turno = models.ForeignKey('programacion_models.ModeloTurno', on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    creado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    # Managers
    objects = ActivoProgramacionManager()  # Solo activos por defecto
    all_objects = models.Manager()         # Todos, incluso inactivos

    def obtener_terceros_activos(self, fecha):
        return Tercero.objects.filter(
            centro_operativo=self.centro_operativo,
            estado_tercero=Tercero.Estado_Activo
        )
    
    def __str__(self):
        return f"Programación {self.centro_operativo} ({self.fecha_inicio} - {self.fecha_fin})"

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.save()

    def restore(self):
        self.activo = True
        self.save()

class AsignacionTurno(models.Model):
    programacion = models.ForeignKey(ProgramacionHorario, on_delete=models.CASCADE, related_name='asignaciones')
    tercero = models.ForeignKey('usuarios.Tercero', on_delete=models.CASCADE)
    dia = models.DateField()
    letra_turno = models.CharField(max_length=2)
    fila = models.PositiveIntegerField(null= False)
    columna = models.PositiveIntegerField(null= False)
    def __str__(self):
        return f"{self.tercero} - {self.dia}: {self.letra_turno}"
    
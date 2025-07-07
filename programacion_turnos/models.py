from django.db import models
from programacion_models.models import ModeloTurno, LetraTurno



class ProgramacionHorario(models.Model):
    centro_operativo = models.ForeignKey('empresas.CentroOperativo', on_delete=models.CASCADE)
    modelo_turno = models.ForeignKey('programacion_models.ModeloTurno', on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    creado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Programación {self.centro_operativo} ({self.fecha_inicio} - {self.fecha_fin})"

class AsignacionTurno(models.Model):
    programacion = models.ForeignKey(ProgramacionHorario, on_delete=models.CASCADE, related_name='asignaciones')
    tercero = models.ForeignKey('usuarios.Tercero', on_delete=models.CASCADE)
    dia = models.DateField()
    letra_turno = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.tercero} - {self.dia}: {self.letra_turno}"
    
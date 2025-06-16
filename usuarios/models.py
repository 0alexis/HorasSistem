from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.core.exceptions import ValidationError

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende el modelo de usuario de Django
    """
    nombre_usuario = models.CharField(max_length=200)
    tercero = models.ForeignKey('Tercero', on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios_usuario'
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

class Rol(models.Model):
    """
    Modelo para manejar roles de usuario
    """
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    permisos = models.ManyToManyField(Permission, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nombre

class Tercero(models.Model):
    id_tercero = models.AutoField(primary_key=True)
    documento = models.CharField(
        max_length=20,
        unique=True,
        error_messages={
            'unique': 'Ya existe un tercero con este documento.'
        }
    )
    nombre_tercero = models.CharField(max_length=200)
    apellido_tercero = models.CharField(max_length=200)
    correo_tercero = models.EmailField(max_length=300)
    cargo = models.ForeignKey(
        'empresas.Cargo',
        on_delete=models.PROTECT,
        related_name='terceros',
        null=True
    )
    centro_operativo = models.ForeignKey(
        'empresas.CentroOperativo',
        on_delete=models.PROTECT,
        related_name='terceros',
        null=True,
        verbose_name='Centro Operativo'
    )
    estado_tercero = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Tercero'
        verbose_name_plural = 'Terceros'

    def __str__(self):
        return f"{self.nombre_tercero} {self.apellido_tercero}"

class CodigoTurno(models.Model):
    TIPO_CHOICES = [
        ('N', 'Normal'),
        ('D', 'Descanso'),
    ]

    id_codigo_turnos = models.AutoField(primary_key=True)
    letra_turno = models.CharField(max_length=10)
    tipo = models.CharField(
        max_length=1, 
        choices=TIPO_CHOICES, 
        default='N'
    )
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_final = models.TimeField(null=True, blank=True)
    estado_codigo = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Código de Turno'
        verbose_name_plural = 'Códigos de Turnos'

    def clean(self):
        if self.tipo == 'D':
            self.hora_inicio = None
            self.hora_final = None
        elif self.tipo == 'N' and (not self.hora_inicio or not self.hora_final):
            raise ValidationError({
                'hora_inicio': 'Los turnos normales requieren hora de inicio y fin'
            })

    def __str__(self):
        if self.tipo == 'D':
            return f"{self.letra_turno} (Descanso)"
        return f"{self.letra_turno} ({self.hora_inicio} - {self.hora_final})"

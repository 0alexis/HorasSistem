from django.contrib.auth.models import AbstractUser, Permission
from django.db import models

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
    documento = models.CharField(max_length=20)
    nombre_tercero = models.CharField(max_length=200)
    apellido_tercero = models.CharField(max_length=200)
    correo_tercero = models.EmailField(max_length=300)
    estado_tercero = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Tercero'
        verbose_name_plural = 'Terceros'

    def __str__(self):
        return f"{self.nombre_tercero} {self.apellido_tercero}"

class CodigoTurno(models.Model):
    id_codigo_turnos = models.AutoField(primary_key=True)
    letra_turno = models.CharField(max_length=10)
    hora_inicio = models.TimeField()
    hora_final = models.TimeField()
    estado_codigo = models.IntegerField(default=1)

    def __str__(self):
        return self.letra_turno

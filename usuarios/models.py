from django.contrib.auth.models import AbstractUser, Permission, Group, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError

# Manager personalizado para soft delete de Usuario
class ActivoUsuarioManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(estado=True)

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        return self.create_user(username, email, password, **extra_fields)

# Manager personalizado para soft delete de Tercero
class ActivoTerceroManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(estado_tercero=1)

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende el modelo de usuario de Django
    """
    nombre_usuario = models.CharField(max_length=200)
    centro_operativo = models.ForeignKey('empresas.CentroOperativo', on_delete=models.PROTECT, null=True, blank=True)
    cargo_predefinido = models.ForeignKey('empresas.CargoPredefinido', on_delete=models.PROTECT, null=True, blank=True)
    tercero = models.ForeignKey('Tercero', on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Managers
    objects = ActivoUsuarioManager()  # Solo activos por defecto
    all_objects = models.Manager()    # Todos, incluso inactivos

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios_usuario'
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

    def delete(self, using=None, keep_parents=False):
        self.estado = False
        self.save()

    def restore(self):
        self.estado = True
        self.save()

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
    cargo_predefinido = models.ForeignKey(
        'empresas.CargoPredefinido',
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
    
    Estado_Activo = 1
    Estado_Inactivo = 0
    estado_tercero = models.IntegerField(default=Estado_Activo)

    # Managers
    objects = ActivoTerceroManager()  # Solo activos por defecto
    all_objects = models.Manager()    # Todos, incluso inactivos

    class Meta:
        verbose_name = 'Tercero'
        verbose_name_plural = 'Terceros'

    def __str__(self):
        return f"{self.nombre_tercero} {self.apellido_tercero}"

    def delete(self, using=None, keep_parents=False):
        self.estado_tercero = self.Estado_Inactivo
        self.save()

    def restore(self):
        self.estado_tercero = self.Estado_Activo
        self.save()

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

def crear_usuario_desde_tercero(tercero, username, password, grupo_nombre):
    """
    Crea un usuario del sistema a partir de un tercero existente.
    """
    # Importa aquí para evitar problemas de importación circular
    from .models import Usuario

    # Busca el grupo de permisos
    grupo = Group.objects.get(name=grupo_nombre)

    usuario = Usuario.objects.create_user(
        username=username,
        password=password,
        nombre_usuario=f"{tercero.nombre_tercero} {tercero.apellido_tercero}",
        tercero=tercero,
        email=tercero.correo_tercero,
        estado=True,
    )
    usuario.cargo_predefinido = tercero.cargo_predefinido  # Si tienes este campo en Usuario
    usuario.centro_operativo = tercero.centro_operativo  # Si tienes este campo en Usuario
    usuario.save()
    usuario.groups.add(grupo)
    return usuario

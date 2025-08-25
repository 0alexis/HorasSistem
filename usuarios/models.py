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
   
    unidad_negocio = models.ForeignKey(
        'empresas.UnidadNegocio',
        on_delete=models.PROTECT,
        related_name='terceros',
        null=True,
        verbose_name='Unidad de Negocio'
    )
    centro_de_costo = models.ForeignKey(
        'CentroDeCosto',
        on_delete=models.PROTECT,
        related_name='terceros',
        null=True,
        verbose_name='Centro de Costo'
    )
    proyecto = models.ForeignKey(
        'empresas.Proyecto',
        on_delete=models.PROTECT,
        related_name='terceros',
        null=True,
        verbose_name='Proyecto'
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
        ('F', 'Festivo'),
        ('FO', 'Festivo Ordinario'),
        ('ND', 'No Devengado'), #ND se usa para las novedades, como dias de medicina y cosas especiales
        ('E', 'Especial'),
    ]
    
    SEGMENTO_TIPOS = [
        ('NORMAL', 'Normal'),
        ('FESTIVO', 'Festivo'),
        ('NOCTURNO', 'Nocturno'),
        ('DOMINGO', 'Domingo'),
        ('EXTRA', 'Extra'),
        ('COMPENSATORIO', 'Compensatorio'),
    ]
    
    # Duración esperada por tipo de turno (min, max) en horas
    DURACIONES_ESPERADAS = {
        'N': (8, 8),      # Normal: exactamente 8 horas
        'F': (6, 10),     # Festivo: entre 6 y 10 horas
        'FO': (6, 10),    # Festivo Ordinario: entre 6 y 10 horas
        'E': (4, 12),     # Especial: entre 4 y 12 horas
        'D': (0, 0),      # Descanso: 0 horas
        'ND': (0, 0),     # No Devengado: 0 horas
    }

    id_codigo_turnos = models.AutoField(primary_key=True)
    letra_turno = models.CharField(max_length=10)
    tipo = models.CharField(
        max_length=2, 
        choices=TIPO_CHOICES, 
        default='N'
    )
    
    # Campos legacy para compatibilidad (se mantienen por ahora)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_final = models.TimeField(null=True, blank=True)
    
    # Nuevo sistema de segmentos
    segmentos_horas = models.JSONField(default=list, blank=True)
    
    # Campo para descripción de novedad (para No Devengado)
    descripcion_novedad = models.CharField(max_length=200, null=True, blank=True)
    
    # Campo para duración total (se autoguarda)
    duracion_total = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True,
        verbose_name='Duración Total (horas)',
        help_text='Duración total del turno en horas (se calcula automáticamente)'
    )
    
    estado_codigo = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Código de Turno'
        verbose_name_plural = 'Códigos de Turnos'

    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar según el tipo de turno
        if self.tipo == 'D':  # Descanso
            self.hora_inicio = None
            self.hora_final = None
            self.segmentos_horas = []
            self.duracion_total = 0
            
        elif self.tipo == 'ND':  # No Devengado
            self.hora_inicio = None
            self.hora_final = None
            self.segmentos_horas = []
            self.duracion_total = 0
            if not self.descripcion_novedad:
                raise ValidationError({
                    'descripcion_novedad': 'Los turnos No Devengado requieren una descripción'
                })
                
        elif self.tipo == 'N':  # Normal
            # Validar que tenga exactamente 1 segmento
            if not self.segmentos_horas or len(self.segmentos_horas) != 1:
                raise ValidationError({
                    'segmentos_horas': 'Los turnos normales deben tener exactamente 1 segmento'
                })
            # Validar que el segmento sea de tipo NORMAL
            if self.segmentos_horas and self.segmentos_horas[0].get('tipo') != 'NORMAL':
                raise ValidationError({
                    'segmentos_horas': 'Los turnos normales solo pueden tener segmentos de tipo NORMAL'
                })
                
        else:  # Festivo, Especial, etc.
            # Validar segmentos
            self.validar_segmentos()
        
        # Calcular y validar duración esperada
        self.calcular_duracion_total()
        self.validar_duracion_esperada()
    
    def save(self, *args, **kwargs):
        """Autoguardar la duración total antes de guardar"""
        # Calcular duración total
        self.calcular_duracion_total()
        super().save(*args, **kwargs)
    
    def calcular_duracion_total(self):
        """Calcular y guardar la duración total del turno"""
        if self.tipo in ['D', 'ND']:
            self.duracion_total = 0
        else:
            duracion = self.get_duracion_total()
            self.duracion_total = duracion
    
    def validar_segmentos(self):
        """Validar que los segmentos sean lógicamente continuos"""
        from django.core.exceptions import ValidationError
        
        if not self.segmentos_horas:
            raise ValidationError({
                'segmentos_horas': 'Los turnos con horarios deben tener al menos 1 segmento'
            })
        
        if len(self.segmentos_horas) > 8:
            raise ValidationError({
                'segmentos_horas': 'No se pueden tener más de 8 segmentos por turno'
            })
        
        # Validar que los segmentos estén ordenados cronológicamente
        segmentos_ordenados = sorted(self.segmentos_horas, key=lambda x: x.get('inicio', ''))
        
        if segmentos_ordenados != self.segmentos_horas:
            raise ValidationError({
                'segmentos_horas': 'Los segmentos deben estar ordenados cronológicamente'
            })
        
        # Validar continuidad (sin gaps)
        for i in range(len(self.segmentos_horas) - 1):
            segmento_actual = self.segmentos_horas[i]
            segmento_siguiente = self.segmentos_horas[i + 1]
            
            if segmento_actual.get('fin') != segmento_siguiente.get('inicio'):
                raise ValidationError({
                    'segmentos_horas': f'Gap detectado entre {segmento_actual.get("fin")} y {segmento_siguiente.get("inicio")}'
                })
        
        # Validar que no haya traslapes
        for i in range(len(self.segmentos_horas)):
            for j in range(i + 1, len(self.segmentos_horas)):
                seg1 = self.segmentos_horas[i]
                seg2 = self.segmentos_horas[j]
                
                # Verificar si hay traslape
                if (seg1.get('inicio') < seg2.get('fin') and 
                    seg1.get('fin') > seg2.get('inicio')):
                    raise ValidationError({
                        'segmentos_horas': f'Traslape detectado entre segmentos {i+1} y {j+1}'
                    })
    
    def validar_duracion_esperada(self):
        """Validar que la duración total cumpla con lo esperado para el tipo"""
        from django.core.exceptions import ValidationError
        
        if self.tipo not in self.DURACIONES_ESPERADAS:
            return
        
        duracion_min, duracion_max = self.DURACIONES_ESPERADAS[self.tipo]
        duracion_actual = self.get_duracion_total()
        
        if duracion_actual < duracion_min or duracion_actual > duracion_max:
            if duracion_min == duracion_max:
                raise ValidationError({
                    'segmentos_horas': f'Los turnos de tipo {self.get_tipo_display()} deben tener exactamente {duracion_min} horas. Duración actual: {duracion_actual:.1f} horas'
                })
            else:
                raise ValidationError({
                    'segmentos_horas': f'Los turnos de tipo {self.get_tipo_display()} deben tener entre {duracion_min} y {duracion_max} horas. Duración actual: {duracion_actual:.1f} horas'
                })
    
    def get_horario_total(self):
        """Obtener el horario total del turno basado en los segmentos"""
        if not self.segmentos_horas:
            return None, None
        
        primer_segmento = self.segmentos_horas[0]
        ultimo_segmento = self.segmentos_horas[-1]
        
        return primer_segmento.get('inicio'), ultimo_segmento.get('fin')
    
    def get_duracion_total(self):
        """Calcular la duración total del turno en horas"""
        if not self.segmentos_horas:
            return 0
        
        from datetime import datetime, timedelta
        
        duracion_total = timedelta()
        
        for segmento in self.segmentos_horas:
            inicio = datetime.strptime(segmento.get('inicio'), '%H:%M').time()
            fin = datetime.strptime(segmento.get('fin'), '%H:%M').time()
            
            # Convertir a datetime para calcular diferencia
            inicio_dt = datetime.combine(datetime.today(), inicio)
            fin_dt = datetime.combine(datetime.today(), fin)
            
            # Si el fin es menor que el inicio, significa que cruza medianoche
            if fin_dt < inicio_dt:
                fin_dt += timedelta(days=1)
            
            duracion_total += fin_dt - inicio_dt
        
        return duracion_total.total_seconds() / 3600  # Convertir a horas
    
    def get_duracion_esperada_info(self):
        """Obtener información sobre la duración esperada para este tipo"""
        if self.tipo not in self.DURACIONES_ESPERADAS:
            return "Sin restricción de duración"
        
        duracion_min, duracion_max = self.DURACIONES_ESPERADAS[self.tipo]
        
        if duracion_min == duracion_max:
            return f"Exactamente {duracion_min} horas"
        else:
            return f"Entre {duracion_min} y {duracion_max} horas"
    
    def __str__(self):
        if self.tipo == 'D':
            return f"{self.letra_turno} (Descanso)"
        elif self.tipo == 'ND':
            return f"{self.letra_turno} (No Devengado: {self.descripcion_novedad})"
        elif self.segmentos_horas:
            inicio, fin = self.get_horario_total()
            duracion = self.get_duracion_total()
            return f"{self.letra_turno} ({inicio}-{fin}, {duracion:.1f}h, {len(self.segmentos_horas)} segmentos)"
        else:
            return f"{self.letra_turno} ({self.hora_inicio}-{self.hora_final})"

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

class CentroDeCosto(models.Model):
    """
    Tabla para centros de costo.
    """
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Centro de Costo'
        verbose_name_plural = 'Centros de Costo'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

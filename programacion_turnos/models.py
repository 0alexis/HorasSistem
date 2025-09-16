from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.conf import settings
from programacion_models.models import ModeloTurno, LetraTurno
from usuarios.models import Tercero, CodigoTurno
from empresas.models import CargoPredefinido
from django.core.exceptions import ValidationError
import re

# Manager personalizado para soft delete de ProgramacionHorario
class ActivoProgramacionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)

class ProgramacionHorario(models.Model):
    # terceros = models.ManyToManyField('usuarios.Tercero', related_name='programaciones')
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la programación")
    centro_operativo = models.ForeignKey('empresas.CentroOperativo', on_delete=models.CASCADE)
    modelo_turno = models.ForeignKey('programacion_models.ModeloTurno', on_delete=models.PROTECT)
    cargo_predefinido = models.ForeignKey('empresas.CargoPredefinido', on_delete=models.PROTECT)
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
    letra_turno = models.CharField(max_length=10)
    fila = models.PositiveIntegerField(null= False)
    columna = models.PositiveIntegerField(null= False)

    class Meta:
        verbose_name = 'Asignación de Turno'
        verbose_name_plural = 'Asignaciones de Turno'
        unique_together = ['programacion', 'tercero', 'dia']


    def clean(self):
        """Validación personalizada"""
        super().clean()

        if self.letra_turno:
            # ✅ PERMITIR CARACTERES ALFANUMÉRICOS Y ALGUNOS ESPECIALES
            patron_valido = r'^[A-Za-z0-9+\-*/&@#.]+$'
            
            if not re.match(patron_valido, self.letra_turno):
                raise ValidationError({
                    'letra_turno': f'El código "{self.letra_turno}" contiene caracteres no válidos. Solo se permiten letras, números y símbolos: + - * / & @ # .'
                })
            

        
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.tercero} - {self.dia}: {self.letra_turno}"



class Bitacora(models.Model):
    TIPOS_ACCION = [
        ('CREAR', 'Crear'),
        ('EDITAR', 'Editar'),
        ('ELIMINAR', 'Eliminar'),
        ('CONSULTAR', 'Consultar'),
    ]
    
    MODULOS = [
        ('programacion', 'Programación'),
        ('turnos', 'Turnos'),
        ('empleados', 'Empleados'),
        ('modelos', 'Modelos de Turno'),
        ('usuarios', 'Usuarios'),
    ]

   #usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Usuario')

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Usuario')
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')
    ip_address = models.GenericIPAddressField(verbose_name='Dirección IP', null=True, blank=True)
    tipo_accion = models.CharField(max_length=20, choices=TIPOS_ACCION, verbose_name='Tipo de Acción')
    modulo = models.CharField(max_length=20, choices=MODULOS, verbose_name='Módulo')
    modelo_afectado = models.CharField(max_length=50, verbose_name='Modelo Afectado')
    objeto_id = models.IntegerField(null=True, blank=True, verbose_name='ID del Objeto')
    descripcion = models.TextField(verbose_name='Descripción')
    valores_anteriores = models.JSONField(null=True, blank=True, verbose_name='Valores Anteriores')
    valores_nuevos = models.JSONField(null=True, blank=True, verbose_name='Valores Nuevos')
    campos_modificados = models.JSONField(null=True, blank=True, verbose_name='Campos Modificados')
    
    class Meta:
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['usuario', 'fecha_hora']),
            models.Index(fields=['tipo_accion', 'fecha_hora']),
            models.Index(fields=['modulo', 'fecha_hora']),
        ]
    
    def __str__(self):
        return f"{self.usuario} - {self.tipo_accion} - {self.modulo} - {self.fecha_hora}"
    
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Empresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)  # Del diagrama
    nombre = models.CharField(max_length=200)
    nit = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    terceros = models.ManyToManyField(
        'usuarios.Tercero',
        through='AsignacionTerceroEmpresa',
        related_name='empresas'
    )

    def __str__(self):
        return f"{self.nombre} - {self.nit}"

# Modelo para UnidadNegocio (UEN)
class UnidadNegocio(models.Model):
    id_uen = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True  # Hacemos opcional el responsable
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    estado_uen = models.IntegerField(default=1)
    empresas = models.ManyToManyField(
        Empresa, 
        related_name='unidades_negocio',
        verbose_name='Empresas',
        blank=True  # Hacemos opcional la relación con empresas
    )

    class Meta:
        verbose_name = 'Unidad de Negocio'
        verbose_name_plural = 'Unidades de Negocio'

    def __str__(self):
        return self.nombre

# Modelo para Proyecto
class Proyecto(models.Model):
    id_proyecto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    id_empresa_proyecto = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='proyectos'
    )
    responsable = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='proyectos_responsable'
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)  # Add this line
    actualizado_en = models.DateTimeField(auto_now=True)  # Add this line

    class Meta:
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return self.nombre

# Modelo para CentroOperativo
class CentroOperativo(models.Model):
    id_centro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    responsable = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='centros_operativos_responsable'
    )
    proyectos = models.ManyToManyField(
        Proyecto,
        related_name='centros_operativos',
        verbose_name='Proyectos'
    )

    class Meta:
        verbose_name = 'Centro Operativo'
        verbose_name_plural = 'Centros Operativos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"

# Modelo para CargoPredefinido
class CargoPredefinido(models.Model):
    NIVEL_CARGO = [
        ('ALTO', 'Nivel Alto'),
        ('MEDIO', 'Nivel Medio'),
        ('OPERATIVO', 'Nivel Operativo'),
    ]

    AREA = [
        ('ADMINISTRATIVA', 'Área Administrativa'),
        ('OPERATIVA', 'Área Operativa'),
        ('COMERCIAL', 'Área Comercial'),
        ('TECNICA', 'Área Técnica'),
        ('OTROS', 'Otras Áreas'),
    ]

    id_cargo_predefinido = models.AutoField(primary_key=True)  # Del diagrama (ajustado)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(help_text="Descripción general de las funciones del cargo")
    nivel = models.CharField(max_length=20, choices=NIVEL_CARGO, default='OPERATIVO', help_text="Nivel jerárquico del cargo")
    area = models.CharField(max_length=20, choices=AREA, default='OTROS', help_text="Área funcional del cargo")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    estado_cargo = models.IntegerField(default=1)  # Del diagrama

    def __str__(self):
        return f"{self.nombre} - {self.get_nivel_display()} ({self.get_area_display()})"

    class Meta:
        verbose_name = 'Cargo Predefinido'
        verbose_name_plural = 'Cargos Predefinidos'
        ordering = ['area', 'nivel', 'nombre']
        unique_together = ['nombre', 'nivel']

# Modelo para Cargo
class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# Modelo para AsignacionTerceroEmpresa
class AsignacionTerceroEmpresa(models.Model):
    tercero = models.ForeignKey('usuarios.Tercero', on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    centro_operativo = models.ForeignKey(
        CentroOperativo, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Asignación de Tercero'
        verbose_name_plural = 'Asignaciones de Terceros'
        unique_together = ('tercero', 'empresa')

    def __str__(self):
        return f"{self.tercero} - {self.empresa}"

from django.contrib import admin
from .models import (
    Empresa, 
    UnidadNegocio, 
    Proyecto, 
    CentroOperativo, 
    CargoPredefinido, 

    AsignacionTerceroEmpresa
)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nit', 'direccion', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'nit', 'email')

    def get_queryset(self, request):
        return Empresa.all_objects.all()

@admin.register(UnidadNegocio)
class UnidadNegocioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'responsable', 'activo')
    list_filter = ('activo', 'responsable')
    search_fields = ('nombre', 'descripcion')
    filter_horizontal = ('empresas',)  # Mantiene la facilidad de asignar empresas
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Estado y Asignaciones', {
            'fields': ('responsable', 'empresas', 'activo', 'estado_uen')
        })
    )

    def get_queryset(self, request):
        return UnidadNegocio.all_objects.all()

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'id_empresa_proyecto', 'responsable', 'activo')
    list_filter = ('activo', 'id_empresa_proyecto', 'responsable')
    search_fields = ('nombre', 'descripcion')
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'id_empresa_proyecto')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Asignaciones', {
            'fields': ('responsable', 'activo')
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['id_empresa_proyecto'].required = True
        return form

    def get_queryset(self, request):
        return Proyecto.all_objects.all()

@admin.register(CentroOperativo)
class CentroOperativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'get_proyectos', 'get_terceros_count', 'responsable', 'activo', 'promesa_valor')
    list_filter = ('activo', 'ciudad', 'proyectos')
    search_fields = ('nombre', 'ciudad', 'proyectos__nombre')
    filter_horizontal = ('proyectos',)

    def get_terceros_count(self, obj):
        return obj.terceros.count()
    get_terceros_count.short_description = 'Terceros'

    def get_proyectos(self, obj):
        return ", ".join([proyecto.nombre for proyecto in obj.proyectos.all()])
    get_proyectos.short_description = 'Proyectos'

    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'direccion', 'ciudad', 'responsable', 'activo', 'promesa_valor')
        }),
        ('Relaciones', {
            'fields': ('proyectos',),
            'classes': ('collapse',)
        }),
    )

@admin.register(CargoPredefinido)
class CargoPredefinidoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'nivel', 'area', 'activo', 'estado_cargo')
    list_filter = ('nivel', 'area', 'activo', 'estado_cargo')
    search_fields = ('nombre', 'descripcion')

    #def get_queryset(self, request):
     #   return CargoPredefinido.all_objects.all()
     #que el ulimo beso sea el de mi madre
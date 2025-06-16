from django.contrib import admin
from .models import (
    Empresa, 
    UnidadNegocio, 
    Proyecto, 
    CentroOperativo, 
    CargoPredefinido, 
    Cargo
)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nit', 'email', 'activo')
    search_fields = ('nombre', 'nit')
    list_filter = ('activo',)

@admin.register(UnidadNegocio)
class UnidadNegocioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'responsable', 'activo')
    list_filter = ('activo', 'estado_uen')
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

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id_empresa_proyecto', 'fecha_inicio', 'responsable', 'activo')
    list_filter = ('activo', 'id_empresa_proyecto')
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

@admin.register(CentroOperativo)
class CentroOperativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'get_proyectos', 'responsable', 'activo')
    list_filter = ('activo', 'ciudad', 'proyectos')
    search_fields = ('nombre', 'ciudad', 'proyectos__nombre')
    filter_horizontal = ('proyectos',)

    def get_proyectos(self, obj):
        return ", ".join([proyecto.nombre for proyecto in obj.proyectos.all()])
    get_proyectos.short_description = 'Proyectos'

    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'direccion', 'ciudad', 'responsable', 'activo')
        }),
        ('Relaciones', {
            'fields': ('proyectos',),
            'classes': ('collapse',)
        }),
    )

@admin.register(CargoPredefinido)
class CargoPredefinidoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nivel', 'area', 'activo')
    list_filter = ('nivel', 'area', 'activo')
    search_fields = ('nombre', 'descripcion')
    ordering = ('area', 'nivel', 'nombre')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('cargo_predefinido', 'centro_operativo', 'activo')
    list_filter = ('cargo_predefinido__nivel', 'cargo_predefinido__area', 'centro_operativo', 'activo')
    search_fields = ('cargo_predefinido__nombre', 'centro_operativo__nombre')
    ordering = ('cargo_predefinido__nivel', 'cargo_predefinido__nombre')
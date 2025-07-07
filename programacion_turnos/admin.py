from django.contrib import admin
from .models import ProgramacionHorario, AsignacionTurno

@admin.register(ProgramacionHorario)
class ProgramacionHorarioAdmin(admin.ModelAdmin):
    list_display = ('centro_operativo', 'modelo_turno', 'fecha_inicio', 'fecha_fin', 'creado_por', 'creado_en')
    search_fields = ('centro_operativo__nombre', 'modelo_turno__nombre')
    list_filter = ('centro_operativo', 'modelo_turno', 'fecha_inicio', 'fecha_fin')

@admin.register(AsignacionTurno)
class AsignacionTurnoAdmin(admin.ModelAdmin):
    list_display = ('programacion', 'tercero', 'dia', 'letra_turno')
    search_fields = ('tercero__nombre_tercero', 'programacion__centro_operativo__nombre')
    list_filter = ('programacion', 'tercero', 'dia', 'letra_turno')

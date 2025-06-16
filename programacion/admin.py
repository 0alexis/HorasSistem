from django.contrib import admin
from .models import ProgramacionTurnos

@admin.register(ProgramacionTurnos)
class ProgramacionTurnosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'centro_operativo', 'fecha_inicio', 'fecha_fin', 'estado')
    list_filter = ('estado', 'centro_operativo')
    search_fields = ('nombre', 'observaciones')
    date_hierarchy = 'fecha_inicio'
    fieldsets = (
        (None, {
            'fields': ('nombre', 'centro_operativo', 'observaciones')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Estado', {
            'fields': ('estado',)
        })
    )

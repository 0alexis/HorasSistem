from django.contrib import admin
from .models import ModeloTurno, LetraTurno
from .forms import ModeloTurnoForm

class LetraTurnoInline(admin.TabularInline):
    model = LetraTurno
    extra = 0
    readonly_fields = ('fila', 'columna', 'valor')
    can_delete = False

@admin.register(ModeloTurno)
class ModeloTurnoAdmin(admin.ModelAdmin):
    form = ModeloTurnoForm
    list_display = ('nombre', 'unidad_negocio', 'tipo')
    search_fields = ('nombre',)
    inlines = [LetraTurnoInline]

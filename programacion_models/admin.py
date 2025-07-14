from django.contrib import admin
from .models import ModeloTurno
from .forms import ModeloTurnoForm

@admin.register(ModeloTurno)
class ModeloTurnoAdmin(admin.ModelAdmin):
    form = ModeloTurnoForm
    list_display = ('nombre', 'unidad_negocio', 'tipo')
    search_fields = ('nombre',)

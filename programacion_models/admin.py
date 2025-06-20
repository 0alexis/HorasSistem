from django.contrib import admin
from django.utils.html import format_html
from .modelos_turnos.patrones_base import PatronBase
from .models import ModeloTurno
from .forms import ModeloTurnoForm




@admin.register(PatronBase)
class PatronBaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_patron', 'descripcion')
    search_fields = ('nombre',)
    exclude = ('matriz',)  # Oculta la matriz en el formulario, ya que se genera automáticamente

@admin.register(ModeloTurno)
class ModeloTurnoAdmin(admin.ModelAdmin):
    form = ModeloTurnoForm
    list_display = ('nombre', 'patron_base', 'centro_operativo', 'unidad_negocio', 'tipo')
    search_fields = ('nombre',)

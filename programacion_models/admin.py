from django.contrib import admin
from django.utils.html import format_html
from .models import ModeloTurno5x3, CargoRequerido

class CargoRequeridoInline(admin.TabularInline):
    model = CargoRequerido
    extra = 1
    min_num = 1
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:  # Si estamos editando un modelo existente
            # Change cargo_set to cargos
            formset.form.base_fields['cargo'].queryset = obj.centro_operativo.cargos.filter(activo=True)
        return formset

@admin.register(ModeloTurno5x3)
class ModeloTurno5x3Admin(admin.ModelAdmin):
    list_display = ('nombre', 'centro_operativo', 'tipo_turno', 'activo')
    list_filter = ('activo', 'tipo_turno', 'centro_operativo')
    search_fields = ('nombre', 'descripcion')
    inlines = [CargoRequeridoInline]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj and 'centro_operativo' in form.base_fields:
            # En lugar de auto-submit, usar JavaScript
            form.base_fields['centro_operativo'].widget.attrs['onchange'] = 'filterCargos(this.value)'
        return form

    class Media:
        js = ('js/cargo_filter.js',)

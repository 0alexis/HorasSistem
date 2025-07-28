from django.contrib import admin
from .models import ModeloTurno
from .forms import ModeloTurnoForm

@admin.register(ModeloTurno)
class ModeloTurnoAdmin(admin.ModelAdmin):
    form = ModeloTurnoForm
    list_display = ('nombre', 'unidad_negocio', 'tipo')
    search_fields = ('nombre',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        original_init = form.__init__
        def custom_init(this, *a, **k):
            original_init(this, *a, **k)
            this.col_count_html = this.render_col_count()
        form.__init__ = custom_init
        return form

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if 'adminform' in context and hasattr(context['adminform'].form, 'col_count_html'):
            context['col_count_html'] = context['adminform'].form.col_count_html
        return super().render_change_form(request, context, add, change, form_url, obj)

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import ModeloTurno5x3

class ModeloTurnoListView(ListView):
    """Vista para listar todos los modelos de turno"""
    model = ModeloTurno5x3
    template_name = 'programacion_models/modelo_list.html'
    context_object_name = 'modelos'
    ordering = ['-creado_en']

class ModeloTurnoDetailView(DetailView):
    """Vista para ver el detalle de un modelo específico"""
    model = ModeloTurno5x3
    template_name = 'programacion_models/modelo_detail.html'
    context_object_name = 'modelo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregamos los cargos requeridos al contexto
        context['cargos_requeridos'] = self.object.cargorequerido_set.select_related('cargo').all()
        return context

# Create your views here.

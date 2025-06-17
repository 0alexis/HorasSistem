from django.shortcuts import render
from django.views.generic import ListView, DetailView
from programacion_models.models import ModeloTurno5x3
from usuarios.models import Tercero  # Corrected import path

class ProgramacionTurnosView(DetailView):
    model = ModeloTurno5x3
    template_name = 'programacion/programacion_turnos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modelo = self.object
        
        # Obtener terceros por cargo
        terceros_por_cargo = {}
        for cargo_req in modelo.cargorequerido_set.all():
            terceros = Tercero.objects.filter(
                centro_operativo=modelo.centro_operativo,
                cargo=cargo_req.cargo,
                estado_tercero=1
            )[:cargo_req.cantidad_requerida]
            terceros_por_cargo[cargo_req.cargo.id] = list(terceros)
        
        # Generar programación
        num_semanas = int(self.request.GET.get('semanas', 1))
        programacion = modelo.generar_programacion(terceros_por_cargo, num_semanas)
        
        context['programacion'] = programacion
        context['dias_semana'] = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        return context

class ModeloTurnoListView(ListView):
    """Vista para listar los modelos de turnos disponibles"""
    model = ModeloTurno5x3
    template_name = 'programacion_models/modelo_list.html'
    context_object_name = 'modelos'
    
    def get_queryset(self):
        """Retorna los modelos ordenados por fecha de creación"""
        return ModeloTurno5x3.objects.select_related('centro_operativo').all()

class ModeloTurnoDetailView(DetailView):
    """Vista para ver el detalle de un modelo específico"""
    model = ModeloTurno5x3
    template_name = 'programacion_models/modelo_detail.html'
    context_object_name = 'modelo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cargos_requeridos'] = self.object.cargorequerido_set.select_related('cargo').all()
        return context

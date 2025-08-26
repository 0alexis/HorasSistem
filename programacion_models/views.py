from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from rest_framework import generics, viewsets
from .models import ModeloTurno
from .serializers import ModeloTurnoSerializer
from .forms import ModeloTurnoForm

class ModeloTurnoViewSet(viewsets.ModelViewSet):
    queryset = ModeloTurno.objects.all()
    serializer_class = ModeloTurnoSerializer

def modeloturno_list(request):
    turnos = ModeloTurno.objects.all().order_by('-creado_en')
    return render(request, 'programacion_models/modeloturno_list.html', {'turnos': turnos})

def modeloturno_detail(request, pk):
    turno = get_object_or_404(ModeloTurno, pk=pk)
    return render(request, 'programacion_models/modeloturno_detail.html', {'turno': turno})

def modeloturno_create(request):
    if request.method == 'POST':
        form = ModeloTurnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Modelo de turno creado correctamente.")
            return redirect('programacion_models:modeloturno_list')
    else:
        form = ModeloTurnoForm()
    return render(request, 'programacion_models/modeloturno_form.html', {'form': form})

def modeloturno_update(request, pk):
    turno = get_object_or_404(ModeloTurno, pk=pk)
    if request.method == 'POST':
        form = ModeloTurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()
            messages.success(request, "Modelo de turno actualizado correctamente.")
            return redirect('programacion_models:modeloturno_list')
    else:
        form = ModeloTurnoForm(instance=turno)
    return render(request, 'programacion_models/modeloturno_form.html', {'form': form, 'turno': turno})



from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import ProgramacionHorario, AsignacionTurno
from .serializers import ProgramacionHorarioSerializer, AsignacionTurnoSerializer
from datetime import timedelta
from usuarios.models import Tercero
from .utils import programar_turnos
from .serializers import generar_asignaciones


class ProgramacionHorarioViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionHorario.objects.all()
    serializer_class = ProgramacionHorarioSerializer

    def perform_create(self, serializer):
        print("Entrando a perform_create de ProgramacionHorarioViewSet")
        programacion = serializer.save()
        print(f"Programacion creada: {programacion}")
        generar_asignaciones(programacion)
        print("Fin de perform_create")
        empleados = list(Tercero.objects.filter(centro_operativo=programacion.centro_operativo))
        programar_turnos(
            programacion.modelo_turno,
            empleados,
            programacion.fecha_inicio,
            programacion.fecha_fin,
            programacion
        )

class AsignacionTurnoViewSet(viewsets.ModelViewSet):
    queryset = AsignacionTurno.objects.all()
    serializer_class = AsignacionTurnoSerializer

def malla_turnos(request, programacion_id):
    programacion = ProgramacionHorario.objects.get(id=programacion_id)
    empleados = list(Tercero.objects.filter(centro_operativo=programacion.centro_operativo))
    fechas = [programacion.fecha_inicio + timedelta(days=i) for i in range((programacion.fecha_fin - programacion.fecha_inicio).days + 1)]
    asignaciones = AsignacionTurno.objects.filter(programacion=programacion)

    # Construir malla: {empleado_id: {fecha: letra}}
    malla = {emp.id_tercero: {fecha: '' for fecha in fechas} for emp in empleados}
    for asignacion in asignaciones:
        malla[asignacion.tercero_id][asignacion.dia] = asignacion.letra_turno

    return render(request, 'malla_turnos.html', {
        'empleados': empleados,
        'fechas': fechas,
        'malla': malla,
    })
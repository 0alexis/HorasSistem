from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import ProgramacionHorario, AsignacionTurno
from .serializers import ProgramacionHorarioSerializer, AsignacionTurnoSerializer
from datetime import timedelta
from usuarios.models import Tercero
from .utils import programar_turnos
from .serializers import generar_asignaciones
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProgramacionExtensionSerializer
from .models import AsignacionTurno, LetraTurno


class ProgramacionHorarioViewSet(viewsets.ModelViewSet):
    queryset = ProgramacionHorario.objects.all()
    serializer_class = ProgramacionHorarioSerializer

    def perform_create(self, serializer):
        #clase que crea y realiza la programacion de turno
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

    @action(detail=True, methods=['post'], url_path='extender')
    def extender(self, request, pk=None):
        """
        Extiende la programación de turnos a un nuevo rango de fechas, asignando turnos solo a empleados activos en cada fecha.
        """
        programacion = self.get_object()
        serializer = ProgramacionExtensionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fecha_inicio_ext = serializer.validated_data['fecha_inicio_ext']
        fecha_fin_ext = serializer.validated_data['fecha_fin_ext']

        # Validar que el nuevo rango no se solape con el existente
        if fecha_inicio_ext <= programacion.fecha_fin:
            return Response(
                {"detail": "La fecha de inicio de la extensión debe ser posterior al fin de la programación actual."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la matriz de letras del modelo de turno
        letras_qs = LetraTurno.objects.filter(modelo_turno=programacion.modelo_turno)
        matriz = {}
        max_fila = 0
        max_col = 0

        for letra in letras_qs:
            matriz[(letra.fila, letra.columna)] = letra.valor
            max_fila = max(max_fila, letra.fila)
            max_col = max(max_col, letra.columna)

        if not matriz:
            return Response(
                {"detail": "No se encontraron letras de turno para el modelo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la última posición de cada tercero en la programación actual
        ultimas_posiciones = {}
        for asignacion in AsignacionTurno.objects.filter(
            programacion=programacion
        ).order_by('tercero_id', '-dia'):
            if asignacion.tercero.id_tercero not in ultimas_posiciones:
                ultimas_posiciones[asignacion.tercero.id_tercero] = {
                    'fila': asignacion.fila,
                    'columna': asignacion.columna,
                    'dia': asignacion.dia
                }

        dias_ext = (fecha_fin_ext - fecha_inicio_ext).days + 1
        nuevas_asignaciones = []
        empleados_con_asignacion = set()

        for i in range(dias_ext):
            fecha = fecha_inicio_ext + timedelta(days=i)

            # Obtener terceros activos en esta fecha
            terceros_activos_en_fecha = programacion.obtener_terceros_activos(fecha)
            
            for tercero in terceros_activos_en_fecha:
                # Buscar la última asignación de este tercero
                ultima = ultimas_posiciones.get(tercero.id_tercero)
                if ultima:
                    fila = ultima['fila']
                    # Calcular días desde la última asignación
                    dias_desde_ultima = (fecha - ultima['dia']).days
                    nueva_columna = (ultima['columna'] + dias_desde_ultima) % (max_col + 1)
                else:
                    # Si es nuevo, asignar la siguiente fila disponible
                    fila = len(ultimas_posiciones) % (max_fila + 1)
                    nueva_columna = i % (max_col + 1)

                letra = matriz.get((fila, nueva_columna))
                if letra:
                    nuevas_asignaciones.append(
                        AsignacionTurno(
                            programacion=programacion,
                            tercero=tercero,
                            dia=fecha,
                            letra_turno=letra,
                            fila=fila,
                            columna=nueva_columna
                        )
                    )
                    empleados_con_asignacion.add(tercero.id_tercero)
                    
                    # Actualizar la última posición para este tercero
                    ultimas_posiciones[tercero.id_tercero] = {
                        'fila': fila,
                        'columna': nueva_columna,
                        'dia': fecha
                    }

        if not nuevas_asignaciones:
            return Response(
                {"detail": "No hay empleados activos en ninguna fecha del rango de extensión."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Bulk create para eficiencia
        AsignacionTurno.objects.bulk_create(nuevas_asignaciones)
        
        # Actualizar el rango de fechas de la programación
        programacion.fecha_fin = fecha_fin_ext
        programacion.save(update_fields=['fecha_fin'])

        return Response(
            {"detail": f"Extensión realizada correctamente para {len(empleados_con_asignacion)} empleados."},
            status=status.HTTP_200_OK
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
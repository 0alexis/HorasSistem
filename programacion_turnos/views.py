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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import EditarMallaRequestSerializer


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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def editar_malla_api(request, programacion_id):
    serializer = EditarMallaRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    cambios = data['cambios']
    programacion = ProgramacionHorario.objects.filter(pk=programacion_id).first()
    if not programacion:
        return Response({'error': 'Programación no encontrada'}, status=status.HTTP_404_NOT_FOUND)
    cambios_realizados = 0
    for cambio in cambios:
        tercero_id = cambio['tercero_id']
        fecha = cambio['fecha']
        letra = cambio['letra']
        asignacion = AsignacionTurno.objects.filter(
            programacion=programacion,
            tercero_id=tercero_id,
            dia=fecha
        ).first()
        if asignacion and letra != asignacion.letra_turno:
            asignacion.letra_turno = letra
            asignacion.save()
            cambios_realizados += 1
    return Response({'mensaje': f'{cambios_realizados} cambios realizados.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intercambiar_terceros_api(request, programacion_id):
    """
    Intercambia dos terceros en una programación, manteniendo sus asignaciones de turnos.
    """
    try:
        programacion = ProgramacionHorario.objects.get(pk=programacion_id)
    except ProgramacionHorario.DoesNotExist:
        return Response({"error": "Programación no encontrada"}, status=status.HTTP_404_NOT_FOUND)
    
    tercero1_id = request.data.get('tercero1_id')
    tercero2_id = request.data.get('tercero2_id')
    
    if not tercero1_id or not tercero2_id:
        return Response({"error": "Debe proporcionar tercero1_id y tercero2_id"}, status=status.HTTP_400_BAD_REQUEST)
    
    if tercero1_id == tercero2_id:
        return Response({"error": "Los terceros deben ser diferentes"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verificar que ambos terceros existen
        tercero1 = Tercero.objects.get(pk=tercero1_id)
        tercero2 = Tercero.objects.get(pk=tercero2_id)
        
        # Obtener las asignaciones de ambos terceros
        asignaciones1 = AsignacionTurno.objects.filter(
            programacion=programacion,
            tercero_id=tercero1_id
        )
        asignaciones2 = AsignacionTurno.objects.filter(
            programacion=programacion,
            tercero_id=tercero2_id
        )
        
        # Intercambiar los terceros en las asignaciones
        for asignacion in asignaciones1:
            asignacion.tercero = tercero2
            asignacion.save()
        
        for asignacion in asignaciones2:
            asignacion.tercero = tercero1
            asignacion.save()
        
        return Response({
            "mensaje": "Terceros intercambiados correctamente",
            "tercero1": {
                "id": tercero1.id_tercero,
                "nombre": f"{tercero1.nombre_tercero} {tercero1.apellido_tercero}",
                "cedula": tercero1.cedula_tercero
            },
            "tercero2": {
                "id": tercero2.id_tercero,
                "nombre": f"{tercero2.nombre_tercero} {tercero2.apellido_tercero}",
                "cedula": tercero2.cedula_tercero
            }
        }, status=status.HTTP_200_OK)
        
    except Tercero.DoesNotExist:
        return Response({"error": "Uno o ambos terceros no existen"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Error al intercambiar terceros: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

@api_view(['GET'])
def test_bitacora(request):
    """Vista de prueba para verificar que la bitácora funciona"""
    from .utils import registrar_bitacora
    
    print("🧪 Probando bitácora manualmente...")
    
    # Crear un registro de prueba
    bitacora = registrar_bitacora(
        request=request,
        tipo_accion='CONSULTAR',
        modulo='programacion',
        modelo_afectado='Test',
        descripcion='Prueba manual de bitácora',
        valores_nuevos={'test': 'valor'}
    )
    
    if bitacora:
        return Response({
            'mensaje': 'Bitácora funcionando correctamente',
            'bitacora_id': bitacora.id,
            'usuario': str(bitacora.usuario) if bitacora.usuario else 'Anónimo',
            'ip': bitacora.ip_address
        })
    else:
        return Response({
            'error': 'Error al crear bitácora'
        }, status=500)
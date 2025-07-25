from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import ProgramacionHorario
from .serializers import ProgramacionExtensionSerializer
from .models import AsignacionTurno, LetraTurno
from datetime import timedelta
from django.urls import path
from django.shortcuts import redirect, get_object_or_404, render
from django.utils.html import format_html
from django.urls import reverse
from .serializers import generar_asignaciones
from usuarios.models import Tercero
from .utils import programar_turnos

class ProgramacionExtensionForm(forms.Form):
    fecha_inicio_ext = forms.DateField(label="Fecha de inicio de extensión")
    fecha_fin_ext = forms.DateField(label="Fecha de fin de extensión")

@admin.register(ProgramacionHorario)
class ProgramacionHorarioAdmin(admin.ModelAdmin):
    list_display = ('centro_operativo', 'modelo_turno', 'fecha_inicio', 'fecha_fin', 'creado_por', 'activo')
    list_filter = ('activo', 'centro_operativo', 'modelo_turno')
    search_fields = ('centro_operativo__nombre', 'modelo_turno__nombre')
    date_hierarchy = 'fecha_inicio'

    def get_queryset(self, request):
        return ProgramacionHorario.all_objects.all()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:programacion_id>/editar_malla/', self.admin_site.admin_view(self.editar_malla_view), name='programacionhorario-editar-malla'),
            path('<int:programacion_id>/extender/', self.admin_site.admin_view(self.extender_programacion_view), name='programacionhorario-extender'),
        ]
        return custom_urls + urls

    def editar_malla_view(self, request, programacion_id):
        programacion = get_object_or_404(ProgramacionHorario, pk=programacion_id)
        empleados = list(Tercero.objects.filter(centro_operativo=programacion.centro_operativo))
        fechas = [programacion.fecha_inicio + timedelta(days=i) for i in range((programacion.fecha_fin - programacion.fecha_inicio).days + 1)]
        asignaciones = AsignacionTurno.objects.filter(programacion=programacion)
        # Construir malla: {empleado_id: {fecha: asignacion}}
        malla = {empleados.id_tercero: {fecha: None for fecha in fechas} for empleados in empleados}
        for asignacion in asignaciones:
            malla[asignacion.tercero_id][asignacion.dia] = asignacion

        # Agrupar empleados verticalmente según el tamaño del modelo
        modelo_turno = programacion.modelo_turno
        tamano_bloque = modelo_turno.letras.values_list('fila', flat=True).distinct().count()
        empleados_agrupados = [empleados[i:i+tamano_bloque] for i in range(0, len(empleados), tamano_bloque)]

        if request.method == 'POST':
            for emp in empleados:
                for fecha in fechas:
                    key = f"letra_{emp.id_tercero}_{fecha}"
                    if key in request.POST:
                        letra = request.POST.get(key, '').strip()
                        asignacion = malla[emp.id_tercero][fecha]
                        if asignacion and (letra != asignacion.letra_turno):
                            print(f"Actualizando {emp} {fecha}: '{asignacion.letra_turno}' -> '{letra}'")

                            asignacion.letra_turno = letra
                            asignacion.save()
                            
            
            from django.contrib import messages
            messages.success(request, "Malla actualizada correctamente.")
            return redirect(request.path)
        return render(request, "admin/editar_malla_programacion.html", {
            "programacion": programacion,
            "empleados": empleados,
            "empleados_agrupados": empleados_agrupados,
            "fechas": fechas,
            "malla": malla,
        })

    def save_model(self, request, obj, form, change):
        empleados = list(Tercero.objects.filter(centro_operativo=obj.centro_operativo))
        from django.contrib import messages
        # Validación previa (sin crear asignaciones)
        centro_operativo = obj.centro_operativo
        modelo_turno = obj.modelo_turno
        pv = getattr(centro_operativo, 'promesa_valor', None)
        tipo = getattr(modelo_turno, 'tipo', None)
        try:
            if tipo == 'F' and pv is not None:
                min_personas = pv * 4
                if len(empleados) < min_personas:
                    raise ValueError(f"Para modelos de tipo FIJO se requieren al menos {min_personas} personas para realizar esta programacion. Solo hay {len(empleados)} empleados disponibles.")
            # Si pasa la validación, guarda el objeto
            super().save_model(request, obj, form, change)
            # Ahora sí crea las asignaciones
            programar_turnos(
                obj.modelo_turno,
                empleados,
                obj.fecha_inicio,
                obj.fecha_fin,
                obj
            )
        except ValueError as e:
            messages.error(request, str(e))

    def extender_programacion(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Por favor selecciona solo una programación para extender.", level=messages.ERROR)
            return redirect(request.META.get('HTTP_REFERER', '/admin/'))
        programacion = queryset.first()
        if "apply" in request.POST:
            form = ProgramacionExtensionForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                serializer = ProgramacionExtensionSerializer(data=data)
                if serializer.is_valid():
                    fecha_inicio_ext = serializer.validated_data['fecha_inicio_ext']
                    fecha_fin_ext = serializer.validated_data['fecha_fin_ext']
                    if fecha_inicio_ext <= programacion.fecha_fin:
                        self.message_user(request, "La fecha de inicio de la extensión debe ser posterior al fin de la programación actual.", level=messages.ERROR)
                        return redirect(request.path)
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
                        self.message_user(request, "No se encontraron letras de turno para el modelo.", level=messages.ERROR)
                        return redirect(request.path)
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
                        empleados_activos_en_fecha = programacion.obtener_terceros_activos(fecha)
                        for empleado in empleados_activos_en_fecha:
                            if empleado.id_tercero in ultimas_posiciones:
                                ultima_pos = ultimas_posiciones[empleado.id_tercero]
                                fila = ultima_pos['fila']
                                dias_desde_ultima = (fecha - ultima_pos['dia']).days
                                nueva_columna = (ultima_pos['columna'] + dias_desde_ultima) % (max_col + 1)
                            else:
                                fila = len(ultimas_posiciones) % (max_fila + 1)
                                nueva_columna = i % (max_col + 1)
                            letra = matriz.get((fila, nueva_columna))
                            if letra:
                                nuevas_asignaciones.append(
                                    AsignacionTurno(
                                        programacion=programacion,
                                        tercero=empleado,
                                        dia=fecha,
                                        letra_turno=letra,
                                        fila=fila,
                                        columna=nueva_columna
                                    )
                                )
                                empleados_con_asignacion.add(empleado.id_tercero)
                                ultimas_posiciones[empleado.id_tercero] = {
                                    'fila': fila,
                                    'columna': nueva_columna,
                                    'dia': fecha
                                }
                    if not nuevas_asignaciones:
                        self.message_user(request, "No hay empleados activos en ninguna fecha del rango de extensión.", level=messages.ERROR)
                        return redirect(request.path)
                    AsignacionTurno.objects.bulk_create(nuevas_asignaciones)
                    programacion.fecha_fin = fecha_fin_ext
                    programacion.save(update_fields=['fecha_fin'])
                    self.message_user(request, f"Extensión realizada correctamente para {len(empleados_con_asignacion)} empleados.", level=messages.SUCCESS)
                    return redirect(request.path)
                else:
                    self.message_user(request, f"Error de validación: {serializer.errors}", level=messages.ERROR)
                    return redirect(request.path)
        else:
            form = ProgramacionExtensionForm()
        from django.shortcuts import render
        return render(request, "admin/extender_programacion.html", {
            "form": form,
            "programacion": programacion
        })
    extender_programacion.short_description = "Extender programación seleccionada"

    def extender_programacion_view(self, request, programacion_id):
        programacion = self.get_object(request, programacion_id)
        return self.extender_programacion(request, queryset=self.model.objects.filter(pk=programacion_id))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context['extra_button'] = format_html(
            '<a class="button" href="{}">Extender programación</a> '
            '<a class="button" href="{}">Editar malla</a>',
            reverse('admin:programacionhorario-extender', args=[object_id]),
            reverse('admin:programacionhorario-editar-malla', args=[object_id])
        )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

@admin.register(AsignacionTurno)
class AsignacionTurnoAdmin(admin.ModelAdmin):
    list_display = ('programacion', 'tercero', 'dia', 'letra_turno', 'fila', 'columna')
    list_filter = ('programacion', 'tercero')
    search_fields = ('programacion__centro_operativo__nombre', 'tercero__nombre_tercero', 'tercero__apellido_tercero')

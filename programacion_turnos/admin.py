from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import ProgramacionHorario
from .serializers import ProgramacionExtensionSerializer
from .models import AsignacionTurno, LetraTurno
from datetime import timedelta
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django.urls import reverse
from .serializers import generar_asignaciones

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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        generar_asignaciones(obj)

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:programacion_id>/extender/',
                self.admin_site.admin_view(self.extender_programacion_view),
                name='programacionhorario-extender',
            ),
        ]
        return custom_urls + urls

    def extender_programacion_view(self, request, programacion_id):
        programacion = self.get_object(request, programacion_id)
        return self.extender_programacion(request, queryset=self.model.objects.filter(pk=programacion_id))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context['extra_button'] = format_html(
            '<a class="button" href="{}">Extender programación</a>',
            reverse('admin:programacionhorario-extender', args=[object_id])
        )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

@admin.register(AsignacionTurno)
class AsignacionTurnoAdmin(admin.ModelAdmin):
    list_display = ('programacion', 'tercero', 'dia', 'letra_turno', 'fila', 'columna')
    list_filter = ('programacion', 'tercero')
    search_fields = ('programacion__centro_operativo__nombre', 'tercero__nombre_tercero', 'tercero__apellido_tercero')

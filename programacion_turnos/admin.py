from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import ProgramacionHorario, AsignacionTurno, Bitacora
from .serializers import ProgramacionExtensionSerializer
from .models import LetraTurno
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
            path('<int:programacion_id>/intercambiar_terceros/', self.admin_site.admin_view(self.intercambiar_terceros_view), name='programacionhorario-intercambiar-terceros'),
        ]
        return custom_urls + urls

    def editar_malla_view(self, request, programacion_id):
        programacion = get_object_or_404(ProgramacionHorario, pk=programacion_id)
        fechas = [programacion.fecha_inicio + timedelta(days=i) for i in range((programacion.fecha_fin - programacion.fecha_inicio).days + 1)]
        
        # Obtener todas las asignaciones de esta programación
        asignaciones = AsignacionTurno.objects.filter(programacion=programacion).select_related('tercero')
        
        # Obtener terceros únicos que tienen asignaciones, ordenados por fila
        terceros_con_asignaciones = asignaciones.values('tercero_id', 'fila').distinct().order_by('fila', 'tercero_id')
        
        # Obtener los terceros completos ordenados por fila
        empleados = []
        for item in terceros_con_asignaciones:
            tercero = Tercero.objects.get(id_tercero=item['tercero_id'])
            empleados.append(tercero)
        
        # Construir malla basada en las asignaciones reales
        malla = {}
        for empleado in empleados:
            malla[empleado.id_tercero] = {fecha: None for fecha in fechas}
        
        for asignacion in asignaciones:
            if asignacion.tercero_id in malla:
                malla[asignacion.tercero_id][asignacion.dia] = asignacion


        # Agrupar empleados por filas reales del modelo de turno
        modelo_turno = programacion.modelo_turno
        filas_modelo = modelo_turno.letras.values_list('fila', flat=True).distinct().order_by('fila')
        
        # Agrupar empleados por fila real del modelo
        empleados_agrupados = []
        filas_empleados = {}
        
        # Agrupar empleados por su fila asignada
        for asignacion in asignaciones:
            fila = asignacion.fila
            tercero_id = asignacion.tercero_id
            if fila not in filas_empleados:
                filas_empleados[fila] = set()
            filas_empleados[fila].add(tercero_id)
        
        # Crear bloques basados en las filas del modelo
        for fila in filas_modelo:
            if fila in filas_empleados:
                terceros_en_fila = []
                for tercero_id in filas_empleados[fila]:
                    tercero = Tercero.objects.get(id_tercero=tercero_id)
                    terceros_en_fila.append(tercero)
                empleados_agrupados.append(terceros_en_fila)

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
# Se realiza el intercambio de terceros, se selecciona el tercero 1 y el tercero 2, se intercambian las letras de turno de los terceros 1 y 2 
# con esto logramos realizar la API funcion de intercambio de terceros, debe en el front
#  hacerse uso de esto buscando como realizaar de manera UX que se cambien
#  los valores del documento, ya que el intercambio se hace segun lo planeado
    def intercambiar_terceros_view(self, request, programacion_id):
        programacion = get_object_or_404(ProgramacionHorario, pk=programacion_id)
        empleados = list(Tercero.objects.filter(centro_operativo=programacion.centro_operativo))
        
        # Agrupar empleados por filas reales del modelo de turno
        modelo_turno = programacion.modelo_turno
        filas_modelo = modelo_turno.letras.values_list('fila', flat=True).distinct().order_by('fila')
        
        # Obtener asignaciones para agrupar por fila real
        asignaciones = AsignacionTurno.objects.filter(programacion=programacion)
        filas_empleados = {}
        
        # Agrupar empleados por su fila asignada
        for asignacion in asignaciones:
            fila = asignacion.fila
            tercero_id = asignacion.tercero_id
            if fila not in filas_empleados:
                filas_empleados[fila] = set()
            filas_empleados[fila].add(tercero_id)
        
        # Crear bloques basados en las filas del modelo
        empleados_agrupados = []
        for fila in filas_modelo:
            if fila in filas_empleados:
                terceros_en_fila = []
                for tercero_id in filas_empleados[fila]:
                    tercero = Tercero.objects.get(id_tercero=tercero_id)
                    terceros_en_fila.append(tercero)
                empleados_agrupados.append(terceros_en_fila)
        
        if request.method == 'POST':
            tercero1_id = request.POST.get('tercero1')
            tercero2_id = request.POST.get('tercero2')
            
            if tercero1_id and tercero2_id and tercero1_id != tercero2_id:
                try:
                    # Verificar que ambos terceros existen
                    tercero1 = Tercero.objects.get(pk=tercero1_id)
                    tercero2 = Tercero.objects.get(pk=tercero2_id)
                    
                    # Verificar que ambos terceros pertenecen al mismo centro operativo
                    if tercero1.centro_operativo != tercero2.centro_operativo:
                        messages.error(request, "Los terceros deben pertenecer al mismo centro operativo.")
                        return redirect(request.path)
                    
                    # Obtener las asignaciones de ambos terceros
                    asignaciones1 = AsignacionTurno.objects.filter(
                        programacion=programacion,
                        tercero=tercero1
                    ).order_by('dia')
                    asignaciones2 = AsignacionTurno.objects.filter(
                        programacion=programacion,
                        tercero=tercero2
                    ).order_by('dia')
                    
                    print(f"Intercambiando letras de turno en admin: {tercero1} <-> {tercero2}")
                    print(f"Asignaciones tercero1: {asignaciones1.count()}")
                    print(f"Asignaciones tercero2: {asignaciones2.count()}")
                    
                    # Guardar las letras de turno originales
                    letras_tercero1_originales = {asig.dia: asig.letra_turno for asig in asignaciones1}
                    letras_tercero2_originales = {asig.dia: asig.letra_turno for asig in asignaciones2}
                    
                    cambios_realizados = 0
                    
                    # Tercero1 recibe letras de tercero2
                    for asignacion in asignaciones1:
                        if asignacion.dia in letras_tercero2_originales:
                            letra_original = asignacion.letra_turno
                            asignacion.letra_turno = letras_tercero2_originales[asignacion.dia]
                            asignacion.save()
                            cambios_realizados += 1
                            print(f"Asignación {asignacion.id} - {tercero1} día {asignacion.dia}: {letra_original} → {asignacion.letra_turno}")
                    
                    # Tercero2 recibe letras de tercero1
                    for asignacion in asignaciones2:
                        if asignacion.dia in letras_tercero1_originales:
                            letra_original = asignacion.letra_turno
                            asignacion.letra_turno = letras_tercero1_originales[asignacion.dia]
                            asignacion.save()
                            cambios_realizados += 1
                            print(f"Asignación {asignacion.id} - {tercero2} día {asignacion.dia}: {letra_original} → {asignacion.letra_turno}")
                    
                    messages.success(request, f"Letras de turno intercambiadas correctamente: {tercero1} <-> {tercero2}. {cambios_realizados} cambios realizados.")
                    return redirect(request.path)
                    
                except Tercero.DoesNotExist:
                    messages.error(request, "Uno o ambos terceros no existen.")
                except Exception as e:
                    print(f"Error al intercambiar letras de turno en admin: {str(e)}")
                    messages.error(request, f"Error al intercambiar letras de turno: {str(e)}")
            else:
                messages.error(request, "Debe seleccionar dos terceros diferentes.")
        
        return render(request, "admin/intercambiar_terceros.html", {
            "programacion": programacion,
            "empleados_agrupados": empleados_agrupados,
            "total_bloques": len(empleados_agrupados),
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
            '<a class="button" href="{}">Editar malla</a> '
            '<a class="button" href="{}">Intercambiar Terceros</a>',
            reverse('admin:programacionhorario-extender', args=[object_id]),
            reverse('admin:programacionhorario-editar-malla', args=[object_id]),
            reverse('admin:programacionhorario-intercambiar-terceros', args=[object_id])
        )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

@admin.register(AsignacionTurno)
class AsignacionTurnoAdmin(admin.ModelAdmin):
    list_display = ('programacion', 'tercero', 'dia', 'letra_turno', 'fila', 'columna')
    list_filter = ('programacion', 'tercero')
    search_fields = ('programacion__centro_operativo__nombre', 'tercero__nombre_tercero', 'tercero__apellido_tercero')

@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_hora', 'tipo_accion', 'modulo', 'modelo_afectado', 'descripcion')
    list_filter = ('tipo_accion', 'modulo', 'usuario', 'fecha_hora')
    search_fields = ('usuario__username', 'descripcion', 'modelo_afectado')
    readonly_fields = ('usuario', 'fecha_hora', 'ip_address', 'tipo_accion', 'modulo', 'modelo_afectado', 
                      'objeto_id', 'descripcion', 'valores_anteriores', 'valores_nuevos', 'campos_modificados')
    date_hierarchy = 'fecha_hora'
    ordering = ('-fecha_hora',)
    
    def has_add_permission(self, request):
        return False  # No permitir crear registros manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # No permitir editar registros
    
    def has_delete_permission(self, request, obj=None):
        return True  # Permitir eliminar registros si es necesario

from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import ProgramacionHorario, AsignacionTurno, Bitacora, LetraTurno, CodigoTurno
from .serializers import ProgramacionExtensionSerializer, generar_asignaciones
from datetime import timedelta
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404, render
from django.utils.html import format_html
from usuarios.models import Tercero, CodigoTurno
from .utils import programar_turnos
from .services.holiday_service import get_holidays_for_range

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
        from datetime import datetime, timedelta

        programacion = get_object_or_404(ProgramacionHorario, pk=programacion_id)

        # ===== MANEJO DE SOLICITUD POST (GUARDAR CAMBIOS) =====
        if request.method == 'POST':
            cambios = 0
            # Se obtienen empleados relacionados con la programación y se generan todas las fechas del rango
            empleados_qs = Tercero.objects.filter(centro_operativo=programacion.centro_operativo,
                estado_tercero=1 )  # Solo activos
            fechas_qs = [programacion.fecha_inicio + timedelta(days=i) for i in range((programacion.fecha_fin - programacion.fecha_inicio).days + 1)]

            for emp in empleados_qs:
                for fecha in fechas_qs:
                    key = f"letra_{emp.id_tercero}_{fecha.strftime('%Y-%m-%d')}"
                    if key in request.POST:
                        letra = request.POST.get(key, '').strip().upper()
                        AsignacionTurno.objects.update_or_create(
                            programacion=programacion,
                            tercero=emp,
                            dia=fecha,
                            defaults={'letra_turno': letra}
                        )
                        cambios += 1

            if cambios > 0:
                messages.success(request, f"Malla actualizada correctamente. Se procesaron {cambios} celdas.")
            else:
                messages.info(request, "No se detectaron cambios para guardar.")

            return redirect(request.path_info)

        # ===== PREPARACIÓN DE DATOS PARA LA VISTA (SOLO GET) =====
        start_date = programacion.fecha_inicio
        end_date = programacion.fecha_fin
        fechas = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Obtener TODOS los empleados activos del centro operativo (no solo los que tienen asignaciones)
        empleados = Tercero.objects.filter(
            centro_operativo=programacion.centro_operativo,
            estado_tercero=1  # Estado activo es 1, no 'A'
        )
        
        # Obtener todas las asignaciones existentes
        asignaciones = AsignacionTurno.objects.filter(programacion=programacion).select_related('tercero')

        # Construcción de la malla: crear celdas vacías para TODOS los empleados
        malla = {emp.id_tercero: {fecha.strftime('%Y-%m-%d'): '' for fecha in fechas} for emp in empleados}
        
        # Llenar la malla con las asignaciones existentes
        for asignacion in asignaciones:
            fecha_str = asignacion.dia.strftime('%Y-%m-%d')
            if asignacion.tercero_id in malla and fecha_str in malla[asignacion.tercero_id]:
                malla[asignacion.tercero_id][fecha_str] = asignacion.letra_turno or ''

        # Agrupar empleados por fila (solo los que tienen asignaciones para determinar la fila)
        empleados_agrupados = []
        bloques_info = []
        filas_empleados = {}
        
        for asignacion in asignaciones:
            if asignacion.fila not in filas_empleados:
                filas_empleados[asignacion.fila] = set()
            filas_empleados[asignacion.fila].add(asignacion.tercero)
        
        # Si no hay asignaciones, crear un bloque con todos los empleados
        if not filas_empleados:
            empleados_agrupados = [list(empleados)]
            bloques_info = [{'numero': 1, 'empleados': len(empleados)}]
        else:
            for fila, emps in sorted(filas_empleados.items()):
                empleados_agrupados.append(list(emps))
                bloques_info.append({'numero': fila, 'empleados': len(emps)})

        # ===== CÓDIGOS DE TURNO DINÁMICOS =====
        codigos_utilizados = asignaciones.exclude(letra_turno__isnull=True)\
                                        .exclude(letra_turno__exact='')\
                                        .values_list('letra_turno', flat=True)\
                                        .distinct().order_by('letra_turno')
        
        codigos_turno_info = []
        for codigo in codigos_utilizados:
            try:
                # Cambia .get() por .filter().first()
                codigo_obj = CodigoTurno.objects.filter(letra_turno=codigo, estado_codigo=1).first()
                if codigo_obj:
                    codigos_turno_info.append({
                        'codigo': codigo_obj.letra_turno,
                        'descripcion': codigo_obj.descripcion_novedad or f'Turno {codigo}',
                        'color': '#d4edda',
                        'horas': float(codigo_obj.duracion_total) if codigo_obj.duracion_total else 0,
                        'tipo': codigo_obj.tipo
                    })
                else:
                    # Si no encuentra ningún código activo, usar valores por defecto
                    codigos_turno_info.append({
                        'codigo': codigo,
                        'descripcion': f'Turno {codigo} (No en DB)',
                        'color': '#f8d7da',
                        'horas': 0,
                        'tipo': 'N'
                    })
            except Exception as e:
                codigos_turno_info.append({
                    'codigo': codigo,
                    'descripcion': f'Turno {codigo} (Error)',
                    'color': '#f8d7da',
                    'horas': 0,
                    'tipo': 'N'
                })

        # ===== INFORMACIÓN PARA FESTIVOS =====
        holiday_dict = get_holidays_for_range(start_date, end_date)
        dias_festivos_str = [d.strftime('%Y-%m-%d') for d in holiday_dict.keys()]
        holiday_info = {d.strftime('%Y-%m-%d'): name for d, name in holiday_dict.items()}

        # ===== CONTEXTO FINAL PARA EL TEMPLATE =====
        context = {
            "programacion": programacion,
            "empleados": empleados,
            "empleados_agrupados": empleados_agrupados,
            "bloques_info": bloques_info,
            "fechas": fechas,  # Convertir a strings
            "malla": malla,
            "codigos_turno": codigos_turno_info,
            "codigos_utilizados": list(codigos_utilizados),
            "dias_festivos": dias_festivos_str,
            "holiday_info": holiday_info,
            "start_date": start_date,
            "end_date": end_date,
        }

        return render(request, "admin/editar_malla_programacion.html", context)

    def intercambiar_terceros_view(self, request, programacion_id):
        programacion = get_object_or_404(ProgramacionHorario, pk=programacion_id)
        empleados = list(Tercero.objects.filter(centro_operativo=programacion.centro_operativo))

        # Agrupar empleados por fila real según el modelo de turno
        modelo_turno = programacion.modelo_turno
        filas_modelo = modelo_turno.letras.values_list('fila', flat=True).distinct().order_by('fila')

        # Obtener asignaciones para agrupar por fila
        asignaciones = AsignacionTurno.objects.filter(programacion=programacion)
        filas_empleados = {}
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
                    tercero1 = Tercero.objects.get(pk=tercero1_id)
                    tercero2 = Tercero.objects.get(pk=tercero2_id)
                    
                    if tercero1.centro_operativo != tercero2.centro_operativo:
                        messages.error(request, "Los terceros deben pertenecer al mismo centro operativo.")
                        return redirect(request.path)
                    
                    asignaciones1 = AsignacionTurno.objects.filter(programacion=programacion, tercero=tercero1).order_by('dia')
                    asignaciones2 = AsignacionTurno.objects.filter(programacion=programacion, tercero=tercero2).order_by('dia')

                    letras_t1 = {a.dia: a.letra_turno for a in asignaciones1}
                    letras_t2 = {a.dia: a.letra_turno for a in asignaciones2}

                    cambios_realizados = 0
                    for asig in asignaciones1:
                        if asig.dia in letras_t2:
                            asig.letra_turno = letras_t2[asig.dia]
                            asig.save()
                            cambios_realizados += 1
                    for asig in asignaciones2:
                        if asig.dia in letras_t1:
                            asig.letra_turno = letras_t1[asig.dia]
                            asig.save()
                            cambios_realizados += 1

                    messages.success(request, f"Letras de turno intercambiadas correctamente: {tercero1} <-> {tercero2}. {cambios_realizados} cambios realizados.")
                    return redirect(request.path)
                except Tercero.DoesNotExist:
                    messages.error(request, "Uno o ambos terceros no existen.")
                except Exception as e:
                    messages.error(request, f"Error al intercambiar letras de turno: {str(e)}")
            else:
                messages.error(request, "Debe seleccionar dos terceros diferentes.")

        return render(request, "admin/intercambiar_terceros.html", {
            "programacion": programacion,
            "empleados_agrupados": empleados_agrupados,
            "total_bloques": len(empleados_agrupados),
        })

    def save_model(self, request, obj, form, change):
        # Obtener empleados del centro operativo con el cargo específico y activos
        from empresas.models import AsignacionTerceroEmpresa
        
        asignaciones_centro = AsignacionTerceroEmpresa.objects.filter(
            centro_operativo=obj.centro_operativo,
            activo=True
        )
        
        empleados = [
            asignacion.tercero for asignacion in asignaciones_centro
            if asignacion.tercero.cargo_predefinido_id == obj.cargo_predefinido.id_cargo_predefinido
            and asignacion.tercero.estado_tercero == 1
        ]
        
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
            
            if len(empleados) == 0:
                raise ValueError(f"No hay empleados con el cargo '{obj.cargo_predefinido.nombre}' en el centro operativo '{obj.centro_operativo.nombre}'.")
        
            # PASO 1: Si pasa la validación, guarda el objeto PRIMERO
            super().save_model(request, obj, form, change)
            
            # PASO 2: Ahora sí crea las asignaciones (solo al crear, no al editar)
            if not change:  # Solo al crear nuevas programaciones
                from .serializers import generar_asignaciones
                generar_asignaciones(obj)
        except ValueError as e:
            messages.error(request, str(e))

    def extender_programacion_view(self, request, programacion_id):
        programacion = self.get_object(request, programacion_id)
        return self.extender_programacion(request, queryset=self.model.objects.filter(pk=programacion_id))

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
                    for asignacion in AsignacionTurno.objects.filter(programacion=programacion).order_by('tercero_id', '-dia'):
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
        return render(request, "admin/extender_programacion.html", {
            "form": form,
            "programacion": programacion
        })

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
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
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

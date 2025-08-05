from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
import json
from .models import Usuario, Tercero, CodigoTurno

class TimeInputMilitar(forms.TimeInput):
    """Widget personalizado para forzar formato militar (00:00 a 23:59)"""
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({
            'type': 'time',
            'step': '900',  # 15 minutos
            'data-format': 'military',
            'min': '00:00',
            'max': '23:59',
            'class': 'time-input-military'
        })
        super().__init__(attrs, format='%H:%M')
    
    def render(self, name, value, attrs=None, renderer=None):
        # Asegurar que el valor esté en formato militar
        if value:
            if hasattr(value, 'strftime'):
                value = value.strftime('%H:%M')
        
        return super().render(name, value, attrs, renderer)

class SegmentoForm(forms.Form):
    """Formulario para un segmento individual"""
    inicio = forms.TimeField(
        label='Hora Inicio', 
        widget=TimeInputMilitar()
    )
    fin = forms.TimeField(
        label='Hora Fin', 
        widget=TimeInputMilitar()
    )
    tipo = forms.ChoiceField(
        label='Tipo de Segmento',
        choices=CodigoTurno.SEGMENTO_TIPOS,
        widget=forms.Select(attrs={'class': 'segmento-tipo'})
    )

class CodigoTurnoForm(forms.ModelForm):
    """Formulario personalizado para CodigoTurno"""
    
    class Meta:
        model = CodigoTurno
        fields = ['letra_turno', 'tipo', 'segmentos_horas', 'duracion_total', 'descripcion_novedad', 'estado_codigo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer el campo segmentos_horas oculto para que se maneje por JavaScript
        self.fields['segmentos_horas'].widget = forms.HiddenInput()
        self.fields['segmentos_horas'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        segmentos_horas = cleaned_data.get('segmentos_horas')
        
        # Validar y corregir formato de horas en segmentos
        if segmentos_horas:
            try:
                if isinstance(segmentos_horas, str):
                    segmentos = json.loads(segmentos_horas)
                else:
                    segmentos = segmentos_horas
                
                # Validar y corregir cada segmento
                for i, segmento in enumerate(segmentos):
                    if isinstance(segmento, dict):
                        # Validar hora de inicio
                        if 'inicio' in segmento and segmento['inicio']:
                            inicio = self.validar_hora_24h(segmento['inicio'])
                            if inicio:
                                segmentos[i]['inicio'] = inicio
                            else:
                                raise ValidationError(f'Segmento {i+1}: Formato de hora de inicio inválido')
                        
                        # Validar hora de fin
                        if 'fin' in segmento and segmento['fin']:
                            fin = self.validar_hora_24h(segmento['fin'])
                            if fin:
                                segmentos[i]['fin'] = fin
                            else:
                                raise ValidationError(f'Segmento {i+1}: Formato de hora de fin inválido')
                
                # Actualizar el campo con los datos corregidos
                cleaned_data['segmentos_horas'] = segmentos
                
            except json.JSONDecodeError:
                raise ValidationError('Formato JSON inválido en segmentos_horas')
            except Exception as e:
                raise ValidationError(f'Error al procesar segmentos: {str(e)}')
        
        if tipo in ['D', 'ND']:
            # Para descanso y no devengado, no se necesitan segmentos
            cleaned_data['segmentos_horas'] = []
        elif not segmentos_horas:
            # Si no hay segmentos pero el tipo lo requiere
            if tipo not in ['D', 'ND']:
                raise ValidationError('Los turnos con horarios deben tener al menos 1 segmento')
        
        return cleaned_data
    
    def validar_hora_militar(self, hora_str):
        """Validar formato de hora militar (00:00 a 23:59) - SIN CONVERSIONES"""
        if not hora_str:
            return None
        
        # Validar formato militar HH:MM con regex específico
        import re
        regex_militar = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        if regex_militar.match(hora_str):
            try:
                horas, minutos = hora_str.split(':')
                hora_num = int(horas)
                minuto_num = int(minutos)
                
                # Validar rango militar (00:00 a 23:59)
                if 0 <= hora_num <= 23 and 0 <= minuto_num <= 59:
                    return f"{hora_num:02d}:{minuto_num:02d}"
                else:
                    return None
            except:
                return None
        else:
            return None
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asegurar que las horas estén en formato militar antes de guardar
        if instance.segmentos_horas:
            for segmento in instance.segmentos_horas:
                if isinstance(segmento, dict):
                    if 'inicio' in segmento and segmento['inicio']:
                        segmento['inicio'] = self.validar_hora_militar(segmento['inicio']) or segmento['inicio']
                    if 'fin' in segmento and segmento['fin']:
                        segmento['fin'] = self.validar_hora_militar(segmento['fin']) or segmento['fin']
        
        if commit:
            instance.save()
        
        return instance

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'nombre_usuario', 'estado')
    list_filter = ('estado', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'nombre_usuario')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('nombre_usuario', 'email', 'tercero')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Estado', {'fields': ('estado',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'nombre_usuario', 'email', 'tercero', 'estado'),
        }),
    )

    def get_queryset(self, request):
        return Usuario.all_objects.all()

@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = ('nombre_tercero', 'apellido_tercero', 'documento', 'cargo_predefinido', 'centro_operativo', 'estado_tercero')
    list_filter = ('estado_tercero', 'cargo_predefinido', 'centro_operativo')
    search_fields = ('nombre_tercero', 'apellido_tercero', 'documento')
    raw_id_fields = ('cargo_predefinido', 'centro_operativo')

    fieldsets = (
        (None, {
            'fields': ('nombre_tercero', 'apellido_tercero', 'documento', 'correo_tercero', 'cargo_predefinido', 'centro_operativo', 'estado_tercero')
        }),
    )

    def get_queryset(self, request):
        return Tercero.all_objects.all()

@admin.register(CodigoTurno)
class CodigoTurnoAdmin(admin.ModelAdmin):
    form = CodigoTurnoForm
    list_display = ('letra_turno', 'tipo', 'get_horario_display', 'get_segmentos_count', 'estado_codigo')
    list_filter = ('tipo', 'estado_codigo')
    search_fields = ('letra_turno', 'descripcion_novedad')
    readonly_fields = ('get_segmentos_info', 'duracion_total')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('letra_turno', 'tipo', 'estado_codigo')
        }),
        ('Configuración de Segmentos', {
            'fields': ('segmentos_horas', 'get_segmentos_info'),
            'classes': ('collapse',),
            'description': 'Configura los segmentos de horarios para este turno usando la interfaz dinámica'
        }),
        ('Información de Duración', {
            'fields': ('duracion_total',),
            'description': 'Duración total calculada automáticamente'
        }),
        ('Información Adicional', {
            'fields': ('descripcion_novedad',),
            'classes': ('collapse',),
            'description': 'Información adicional para turnos No Devengado'
        }),
    )
    
    def get_horario_display(self, obj):
        """Muestra el horario total del turno"""
        if obj.tipo == 'D':
            return 'Descanso'
        elif obj.tipo == 'ND':
            return f'No Devengado: {obj.descripcion_novedad}'
        elif obj.segmentos_horas:
            inicio, fin = obj.get_horario_total()
            return f"{inicio} - {fin}"
        else:
            return f"{obj.hora_inicio} - {obj.hora_final}"
    get_horario_display.short_description = 'Horario'
    
    def get_segmentos_count(self, obj):
        """Muestra la cantidad de segmentos"""
        if obj.tipo in ['D', 'ND']:
            return 0
        return len(obj.segmentos_horas)
    get_segmentos_count.short_description = 'Segmentos'
    
    def get_segmentos_info(self, obj):
        """Muestra información detallada de los segmentos"""
        if not obj.segmentos_horas:
            return "Sin segmentos configurados"
        
        html = "<div class='segmentos-info'>"
        html += "<h4>Segmentos Configurados:</h4>"
        html += "<table class='segmentos-table'>"
        html += "<tr><th>#</th><th>Inicio</th><th>Fin</th><th>Tipo</th><th>Duración</th></tr>"
        
        for i, segmento in enumerate(obj.segmentos_horas, 1):
            inicio = segmento.get('inicio', '')
            fin = segmento.get('fin', '')
            tipo = segmento.get('tipo', '')
            
            # Calcular duración
            from datetime import datetime
            try:
                inicio_dt = datetime.strptime(inicio, '%H:%M')
                fin_dt = datetime.strptime(fin, '%H:%M')
                if fin_dt < inicio_dt:
                    fin_dt = fin_dt.replace(day=fin_dt.day + 1)
                duracion = fin_dt - inicio_dt
                duracion_str = f"{duracion.seconds // 3600}h {(duracion.seconds % 3600) // 60}m"
            except:
                duracion_str = "N/A"
            
            html += f"<tr><td>{i}</td><td>{inicio}</td><td>{fin}</td><td>{tipo}</td><td>{duracion_str}</td></tr>"
        
        html += "</table>"
        html += f"<p><strong>Duración Total:</strong> {obj.get_duracion_total():.1f} horas</p>"
        html += "</div>"
        
        return format_html(html)
    get_segmentos_info.short_description = 'Información de Segmentos'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('segmentos/', self.admin_site.admin_view(self.segmentos_view), name='codigoturno_segmentos'),
        ]
        return custom_urls + urls
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Usar template personalizado para el formulario de cambio"""
        extra_context = extra_context or {}
        extra_context['show_save'] = True
        extra_context['show_save_and_continue'] = True
        extra_context['show_save_and_add_another'] = False
        return super().change_view(request, object_id, form_url, extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        """Usar template personalizado para el formulario de agregar"""
        extra_context = extra_context or {}
        extra_context['show_save'] = True
        extra_context['show_save_and_continue'] = True
        extra_context['show_save_and_add_another'] = False
        return super().add_view(request, form_url, extra_context)
    
    def segmentos_view(self, request):
        """Vista para manejar segmentos via AJAX"""
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                segmentos = data.get('segmentos', [])
                
                # Validar segmentos
                if len(segmentos) > 8:
                    return JsonResponse({'error': 'Máximo 8 segmentos permitidos'}, status=400)
                
                # Validar continuidad
                for i in range(len(segmentos) - 1):
                    if segmentos[i]['fin'] != segmentos[i + 1]['inicio']:
                        return JsonResponse({
                            'error': f'Gap detectado entre {segmentos[i]["fin"]} y {segmentos[i + 1]["inicio"]}'                                                                                             
                        }, status=400)
                
                return JsonResponse({'success': True, 'segmentos': segmentos})
                
            except json.JSONDecodeError:
                return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        return JsonResponse({'error': 'Método no permitido'}, status=405)

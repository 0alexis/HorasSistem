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

class SegmentoForm(forms.Form):
    """Formulario para un segmento individual"""
    inicio = forms.TimeField(label='Hora Inicio', widget=forms.TimeInput(attrs={'type': 'time'}))
    fin = forms.TimeField(label='Hora Fin', widget=forms.TimeInput(attrs={'type': 'time'}))
    tipo = forms.ChoiceField(
        label='Tipo de Segmento',
        choices=CodigoTurno.SEGMENTO_TIPOS,
        widget=forms.Select(attrs={'class': 'segmento-tipo'})
    )

class CodigoTurnoForm(forms.ModelForm):
    """Formulario personalizado para CodigoTurno"""
    segmentos_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        help_text='JSON de segmentos (se genera automáticamente)'
    )
    
    class Meta:
        model = CodigoTurno
        fields = ['letra_turno', 'tipo', 'segmentos_horas', 'duracion_total', 'descripcion_novedad', 'estado_codigo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Cargar segmentos existentes
            self.fields['segmentos_json'].initial = json.dumps(self.instance.segmentos_horas)
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        segmentos_json = cleaned_data.get('segmentos_json')
        
        if tipo in ['D', 'ND']:
            # Para descanso y no devengado, no se necesitan segmentos
            cleaned_data['segmentos_horas'] = []
        elif segmentos_json:
            try:
                segmentos = json.loads(segmentos_json)
                cleaned_data['segmentos_horas'] = segmentos
            except json.JSONDecodeError:
                raise ValidationError('Formato JSON inválido en segmentos')
        
        return cleaned_data

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
            'fields': ('segmentos_horas', 'segmentos_json', 'get_segmentos_info'),
            'classes': ('collapse',),
            'description': 'Configura los segmentos de horarios para este turno'
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
    
    class Media:
        css = {
            'all': ('/static/admin/css/codigo_turno.css',)
        }
        js = ('/static/admin/js/codigo_turno.js',)
    
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

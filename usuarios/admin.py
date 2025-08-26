from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.core.exceptions import ValidationError
from .models import CentroDeCosto, Usuario, Tercero, CodigoTurno

class TimeInputSimple(forms.TimeInput):
    """Widget simple para formato 24 horas"""
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({
            'type': 'time',
            'step': '900',  # 15 minutos
            'min': '00:00',
            'max': '23:59'
        })
        super().__init__(attrs, format='%H:%M')
    def render(self, name, value, attrs=None, renderer=None):
        if value and hasattr(value, 'strftime'):
            value = value.strftime('%H:%M')
        return super().render(name, value, attrs, renderer)

class CodigoTurnoForm(forms.ModelForm):
    """Formulario para CodigoTurno simplificado"""
    class Meta:
        model = CodigoTurno
        fields = ['letra_turno', 'tipo', 'hora_inicio', 'hora_final', 'duracion_total', 'descripcion_novedad', 'estado_codigo']
        widgets = {
            'hora_inicio': TimeInputSimple(),
            'hora_final': TimeInputSimple(),
        }

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
    list_display = (
        'nombre_tercero', 'apellido_tercero', 'documento',
        'centro_de_costo', 'unidad_negocio', 'centro_operativo', 'proyecto', 'estado_tercero'
    )
    list_filter = ('centro_de_costo', 'unidad_negocio', 'centro_operativo', 'proyecto', 'estado_tercero')
    search_fields = ('nombre_tercero', 'apellido_tercero', 'documento')
    raw_id_fields = ('cargo_predefinido', 'centro_operativo', 'unidad_negocio', 'proyecto', 'centro_de_costo')
    fieldsets = (
        (None, {
            'fields': (
                'nombre_tercero', 'apellido_tercero', 'documento', 'correo_tercero',
                'cargo_predefinido', 'centro_de_costo', 'unidad_negocio', 'centro_operativo', 'proyecto', 'estado_tercero'
            )
        }),
    )
    def get_queryset(self, request):
        return Tercero.all_objects.all()

@admin.register(CentroDeCosto)
class CentroDeCostoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre')

@admin.register(CodigoTurno)
class CodigoTurnoAdmin(admin.ModelAdmin):
    form = CodigoTurnoForm
    list_display = ('letra_turno', 'tipo', 'get_horario_display', 'duracion_total', 'estado_codigo')
    list_filter = ('tipo', 'estado_codigo')
    search_fields = ('letra_turno', 'descripcion_novedad')
    readonly_fields = ('duracion_total',)
    fieldsets = (
        ('Información Básica', {
            'fields': ('letra_turno', 'tipo', 'hora_inicio', 'hora_final', 'estado_codigo')
        }),
        ('Información Adicional', {
            'fields': ('duracion_total', 'descripcion_novedad'),
            'classes': ('collapse',)
        }),
    )
    def get_horario_display(self, obj):
        """Muestra el horario total del turno"""
        if obj.tipo == 'D':
            return 'Descanso'
        elif obj.tipo == 'ND':
            return f'No Devengado: {obj.descripcion_novedad}'
        elif obj.hora_inicio and obj.hora_final:
            return f"{obj.hora_inicio.strftime('%H:%M')} - {obj.hora_final.strftime('%H:%M')}"
        else:
            return "Sin horario"
    get_horario_display.short_description = 'Horario'

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
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

@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = ('nombre_tercero', 'apellido_tercero', 'documento', 'cargo', 'centro_operativo', 'estado_tercero')
    list_filter = ('estado_tercero', 'cargo', 'centro_operativo')
    search_fields = ('nombre_tercero', 'apellido_tercero', 'documento')
    raw_id_fields = ('cargo', 'centro_operativo')

    fieldsets = (
        (None, {
            'fields': ('documento', 'nombre_tercero', 'apellido_tercero', 'correo_tercero')
        }),
        ('Asignaciones', {
            'fields': ('cargo', 'centro_operativo')
        }),
        ('Estado', {
            'fields': ('estado_tercero',)
        })
    )

@admin.register(CodigoTurno)
class CodigoTurnoAdmin(admin.ModelAdmin):
    list_display = ('letra_turno', 'tipo', 'get_horario', 'estado_codigo')
    list_filter = ('tipo', 'estado_codigo')
    search_fields = ('letra_turno',)

    def get_horario(self, obj):
        if obj.tipo == 'D':
            return 'Descanso'
        return f"{obj.hora_inicio} - {obj.hora_final}"
    get_horario.short_description = 'Horario'

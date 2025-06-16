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
    list_display = ('nombre_tercero', 'apellido_tercero', 'documento', 'estado_tercero')
    list_filter = ('estado_tercero',)  # Removido 'id_empresa_tercero'
    search_fields = ('nombre_tercero', 'apellido_tercero', 'documento')

    def get_empresas(self, obj):
        return ", ".join([asignacion.empresa.nombre for asignacion in obj.empresas.through.objects.filter(tercero=obj)])
    get_empresas.short_description = 'Empresas'

@admin.register(CodigoTurno)
class CodigoTurnoAdmin(admin.ModelAdmin):
    list_display = ('letra_turno', 'hora_inicio', 'hora_final', 'estado_codigo')
    list_filter = ('estado_codigo',)
    search_fields = ('letra_turno',)

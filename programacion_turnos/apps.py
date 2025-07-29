from django.apps import AppConfig


class ProgramacionTurnosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'programacion_turnos'
    verbose_name = 'Programación de Turnos'

    def ready(self):
        import programacion_turnos.signals

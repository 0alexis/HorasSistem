from django.core.management.base import BaseCommand
from programacion_turnos.auto_bitacora import obtener_modelos_rastreados, registrar_todos_los_modelos
from programacion_turnos.models import Bitacora

class Command(BaseCommand):
    help = 'Verifica el estado de la bitácora automática del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--registrar',
            action='store_true',
            help='Registrar todos los modelos en la bitácora',
        )
        parser.add_argument(
            '--estado',
            action='store_true',
            help='Mostrar el estado actual de la bitácora',
        )

    def handle(self, *args, **options):
        if options['registrar']:
            self.stdout.write(self.style.SUCCESS('🔄 Registrando todos los modelos en la bitácora...'))
            modelos = registrar_todos_los_modelos()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {len(modelos)} modelos registrados en la bitácora')
            )
            
        if options['estado']:
            self.mostrar_estado()
        elif not options['registrar']:
            self.mostrar_estado()

    def mostrar_estado(self):
        """Muestra el estado actual de la bitácora"""
        self.stdout.write(self.style.SUCCESS('\n📊 ESTADO DE LA BITÁCORA'))
        self.stdout.write('=' * 50)
        
        # Información general
        total_registros = Bitacora.objects.count()
        self.stdout.write(f'📝 Total de registros en bitácora: {total_registros}')
        
        # Modelos rastreados
        modelos = obtener_modelos_rastreados()
        self.stdout.write(f'\n🎯 Modelos rastreados: {len(modelos)}')
        
        # Agrupar por app
        apps = {}
        for modelo in modelos:
            app = modelo['app']
            if app not in apps:
                apps[app] = []
            apps[app].append(modelo['verbose_name'])
        
        for app, modelos_app in apps.items():
            self.stdout.write(f'\n📁 {app.upper()}:')
            for modelo in modelos_app:
                self.stdout.write(f'  • {modelo}')
        
        # Estadísticas por módulo
        self.stdout.write(f'\n📈 Estadísticas por módulo:')
        from django.db.models import Count
        stats = Bitacora.objects.values('modulo').annotate(
            total=Count('id')
        ).order_by('-total')
        
        for stat in stats:
            self.stdout.write(f'  • {stat["modulo"]}: {stat["total"]} registros')
        
        self.stdout.write('\n' + '=' * 50) 
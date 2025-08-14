from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

from empresas.models import Empresa, Proyecto, CentroOperativo
from usuarios.models import Tercero

def custom_logout(request):
    """Cerrar sesión inmediatamente y redirigir al login"""
    logout(request)
    return redirect('/admin/login/')

def home_redirect(request):
    """Redirigir al welcome si está autenticado, sino al admin"""
    if request.user.is_authenticated:
        return redirect('welcome')
    return redirect('admin:index')

@login_required
def welcome_view(request):
    context = {
        # Empresas
        'empresas_activas': Empresa.objects.filter(activo=True).count(),
        'total_empresas': Empresa.objects.count(),
        
        # Proyectos
        'proyectos_activos': Proyecto.objects.filter(activo=True).count(),
        'total_proyectos': Proyecto.objects.count(),
        
        # Centros Operativos
        'centro_operativo': CentroOperativo.objects.filter(activo=1).count(),
        'total_centros_operativos': CentroOperativo.objects.count(),
        
        # Empleados (Terceros)
        'Terceros_activos': Tercero.objects.filter(estado_tercero=1).count(),
        'total_terceros': Tercero.objects.count(),

        # Usuario actual
        'user': request.user,
    }
    
    return render(request, 'admin/welcome.html', context)
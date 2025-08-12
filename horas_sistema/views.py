from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    """Cerrar sesión inmediatamente y redirigir al login"""
    logout(request)  # Cierra la sesión del usuario actual
    return redirect('/admin/login/')  # Redirige al login personalizado
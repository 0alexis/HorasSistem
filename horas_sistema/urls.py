"""
URL configuration for horas_sistema project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from programacion_turnos.views import asignacion_turno_edit_view
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Horas Sistema API",
        default_version='v1',
        description="API Documentation for Horas Sistema",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],
)

# Vista para redirigir la raíz
def home_redirect(request):
    """Redirigir la raíz al welcome si está autenticado, sino al admin"""
    if request.user.is_authenticated:
        return redirect('welcome')
    return redirect('admin:index')

urlpatterns = [
    # ========== RUTAS PRINCIPALES ==========
    path('', home_redirect, name='home'),  # Ruta raíz
    
    # ========== ADMINISTRACIÓN ==========
    path('admin/logout/', views.custom_logout, name='admin_logout'),  
    path('admin/', admin.site.urls),
    
    # ========== DASHBOARD WEB ==========
    path('welcome/', views.welcome_view, name='welcome'),
    path('logout/', views.custom_logout, name='logout'),
    
    # ========== APLICACIONES (CRUD COMPLETO) ==========
    # Una sola ruta para empresas que incluye tanto el CRUD web como las APIs
    path('empresas/', include('empresas.urls')),  # CRUD completo de empresas
    
    # Cuando estén listas, descomenta estas:
    # path('turnos/', include('turnos.urls')),      # CRUD completo de turnos



    # path('terceros/', include('terceros.urls')),  # CRUD completo de terceros
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),
   



    path('asignacionturno/<str:llave>/change/', asignacion_turno_edit_view, name='asignacion_turno_edit'),



     # ========== DASHBOARD PROGRAMACIONES ==========
    path('programacion_turnos/', include('programacion_turnos.urls')),









    # ========== APIs ESPECÍFICAS (OTRAS APLICACIONES) ==========
    # Solo para aplicaciones que no tienen CRUD web o son específicamente APIs
  
    path('api/modelos/', include('programacion_models.urls')),
    path('api/', include('programacion_turnos.urls')),
    
    # ========== DOCUMENTACIÓN API ==========
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

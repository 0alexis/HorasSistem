from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    # ========== DASHBOARD DE EMPRESAS ==========
    path('', views.empresas_dashboard, name='dashboard'),
    
    # ========== CRUD DE EMPRESAS ==========
    path('empresas/', views.empresas_list, name='empresas_list'),  
    path('empresas/nueva/', views.empresa_create, name='empresa_create'),
    path('empresas/<int:pk>/', views.empresa_detail, name='empresa_detail'),
    path('empresas/<int:pk>/editar/', views.empresa_update, name='empresa_update'),
    path('empresas/<int:pk>/eliminar/', views.empresa_delete, name='empresa_delete'),
    
    # ========== CRUD DE PROYECTOS ==========
    path('proyectos/', views.proyectos_list, name='proyectos_list'),
    path('proyectos/nuevo/', views.proyecto_create, name='proyecto_create'),
    path('proyectos/<int:pk>/', views.proyecto_detail, name='proyecto_detail'),
    path('proyectos/<int:pk>/editar/', views.proyecto_update, name='proyecto_update'),
    path('proyectos/<int:pk>/eliminar/', views.proyecto_delete, name='proyecto_delete'),
    
    # ========== CRUD DE CENTROS OPERATIVOS ==========
    path('centros-operativos/', views.centros_operativos_list, name='centros_operativos_list'),
    path('centros-operativos/nuevo/', views.centro_operativo_create, name='centro_operativo_create'),
    path('centros-operativos/<int:pk>/', views.centro_operativo_detail, name='centro_operativo_detail'),
    path('centros-operativos/<int:pk>/editar/', views.centro_operativo_update, name='centro_operativo_update'),
    path('centros-operativos/<int:pk>/eliminar/', views.centro_operativo_delete, name='centro_operativo_delete'),

    # ========== CRUD DE UNIDADES DE NEGOCIO ==========
    path('unidades-negocio/', views.unidades_negocio_list, name='unidades_negocio_list'),
    path('unidades-negocio/nueva/', views.unidad_negocio_create, name='unidad_negocio_create'),
    path('unidades-negocio/<int:pk>/', views.unidad_negocio_detail, name='unidad_negocio_detail'),
    path('unidades-negocio/<int:pk>/editar/', views.unidad_negocio_update, name='unidad_negocio_update'),
    path('unidades-negocio/<int:pk>/eliminar/', views.unidad_negocio_delete, name='unidad_negocio_delete'),
    
    # ========== CRUD DE CARGOS PREDEFINIDOS ==========
    path('cargos/', views.CargoPredefinidoListView.as_view(), name='cargopredefinido_list'),
    path('cargos/crear/', views.CargoPredefinidoCreateView.as_view(), name='cargopredefinido_create'),
    path('cargos/<int:pk>/', views.CargoPredefinidoDetailView.as_view(), name='cargopredefinido_detail'),
    path('cargos/<int:pk>/editar/', views.CargoPredefinidoUpdateView.as_view(), name='cargopredefinido_update'),
    path('cargos/<int:pk>/eliminar/', views.CargoPredefinidoDeleteView.as_view(), name='cargopredefinido_delete'),
    
    # ========== APIs BÁSICAS ==========
    path('api/health/', views.database_health_check, name='api_health_check'),
    path('api/debug-models/', views.debug_models_info, name='api_debug_models'),
    path('api/empresas-activas/', views.empresas_activas_api, name='api_empresas_activas'),
]
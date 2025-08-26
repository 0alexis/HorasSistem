from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UsuarioViewSet, RolViewSet

app_name = 'usuarios'

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'roles', RolViewSet, basename='rol')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    #######usuarios-empleados######
    path('tercero/nuevo/', views.tercero_create, name='tercero_create'),
    path('tercero/', views.tercero_list, name='tercero_list'),  
    path('tercero/<int:pk>/', views.tercero_detail, name='tercero_detail'),  
    path('tercero/<int:pk>/editar/', views.tercero_update, name='tercero_update'), 



    #######centros de costo######
    path('centrodecosto/nuevo/', views.centrodecosto_create, name='centrodecosto_create'),
    path('centrodecosto/', views.centrodecosto_list, name='centrodecosto_list'),
    path('centrodecosto/<int:pk>/', views.centrodecosto_detail, name='centrodecosto_detail'),
    path('centrodecosto/<int:pk>/editar/', views.centrodecosto_update, name='centrodecosto_update'),



    ############CGRUPOS DE PERMISOS############
    path('grupo/nuevo/', views.group_create, name='group_create'),
    path('grupo/', views.group_list, name='group_list'),
    path('grupo/<int:pk>/', views.group_detail, name='group_detail'),
    path('grupo/<int:pk>/editar/', views.group_update, name='group_update'),

    ############VIEW PARA CODIGO DE TURNOS############
    path('codigoturno/nuevo/', views.codigoturno_create, name='codigoturno_create'),
    path('codigoturno/', views.codigoturno_list, name='codigoturno_list'),
    path('codigoturno/<int:pk>/', views.codigoturno_detail, name='codigoturno_detail'),
    path('codigoturno/<int:pk>/editar/', views.codigoturno_update, name='codigoturno_update'),
]
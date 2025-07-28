from .views import EmpresaViewSet, UnidadNegocioViewSet, ProyectoViewSet, CentroOperativoViewSet, CargoPredefinidoViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet)
router.register(r'unidades-negocio', UnidadNegocioViewSet)
router.register(r'proyectos', ProyectoViewSet)
router.register(r'centros-operativos', CentroOperativoViewSet)
router.register(r'cargos-predefinidos', CargoPredefinidoViewSet)

urlpatterns = router.urls
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PruebaViewSet

router = DefaultRouter()
router.register(r'pruebas', PruebaViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 
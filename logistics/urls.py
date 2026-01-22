from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgentCommercialViewSet, ClientViewSet, CommandeViewSet,
    LivraisonViewSet, DashboardViewSet, LogActiviteViewSet
)

router = DefaultRouter()
router.register(r'agents', AgentCommercialViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'commandes', CommandeViewSet)
router.register(r'livraisons', LivraisonViewSet)
router.register(r'logs', LogActiviteViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]

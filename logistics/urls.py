from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgentCommercialViewSet, ClientViewSet, CommandeViewSet,
    LivraisonViewSet, LogActiviteViewSet, TricycleViewSet
)
from .cartography_views import (
    DeliveryMarkersView, AgentPositionsView, ServiceZonesView,
    HeatmapDataView, OptimizedRoutesView, ZoneListView,
    AgentListView, StatsSummaryView
)

router = DefaultRouter()
router.register(r'agents', AgentCommercialViewSet)
router.register(r'tricycles', TricycleViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'commandes', CommandeViewSet)
router.register(r'orders', CommandeViewSet, basename='orders')
router.register(r'livraisons', LivraisonViewSet)
router.register(r'logs', LogActiviteViewSet)

# Cartography/Map endpoints (different namespace to avoid conflicts)
cartography_patterns = [
    path('cartography/livraisons', DeliveryMarkersView.as_view(), name='cartography-deliveries'),
    path('cartography/agents', AgentPositionsView.as_view(), name='cartography-agents'),
    path('cartography/zones', ServiceZonesView.as_view(), name='cartography-zones'),
    path('cartography/zones/list', ZoneListView.as_view(), name='cartography-zones-list'),
    path('cartography/agents/list', AgentListView.as_view(), name='cartography-agents-list'),
    path('cartography/heatmap', HeatmapDataView.as_view(), name='cartography-heatmap'),
    path('cartography/routes', OptimizedRoutesView.as_view(), name='cartography-routes'),
    path('cartography/stats/summary', StatsSummaryView.as_view(), name='cartography-stats'),
]

urlpatterns = [
    path('', include(router.urls)),
] + cartography_patterns

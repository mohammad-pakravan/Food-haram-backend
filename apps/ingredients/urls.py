from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import IngredientManagementViewSet
from .inventory_views import (
    InventoryStockViewSet, 
    InventoryLogViewSet,
    MaterialConsumptionViewSet,
    InventoryStockUpdateViewSet,
    InventoryComparisonView
)

router = DefaultRouter()
router.register(r'stock', InventoryStockViewSet, basename='inventory-stock')
router.register(r'logs', InventoryLogViewSet, basename='inventory-logs')
router.register(r'material-consumptions', MaterialConsumptionViewSet, basename='material-consumption')
router.register(r'stock-updates', InventoryStockUpdateViewSet, basename='inventory-stock-update')
router.register(r'', IngredientManagementViewSet, basename='ingredient-management')

urlpatterns = [
    path('comparison/', InventoryComparisonView.as_view(), name='inventory-comparison'),
] + router.urls

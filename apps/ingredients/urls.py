from rest_framework.routers import DefaultRouter

from .views import IngredientManagementViewSet
from .inventory_views import InventoryStockViewSet, InventoryLogViewSet

router = DefaultRouter()
router.register(r'stock', InventoryStockViewSet, basename='inventory-stock')
router.register(r'logs', InventoryLogViewSet, basename='inventory-logs')
router.register(r'', IngredientManagementViewSet, basename='ingredient-management')

urlpatterns = router.urls

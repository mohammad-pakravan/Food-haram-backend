from rest_framework.routers import DefaultRouter

from .views import DessertViewSet, FoodManagementViewSet

router = DefaultRouter()
router.register(r'desserts', DessertViewSet, basename='dessert-management')
router.register(r'', FoodManagementViewSet, basename='food-management')

urlpatterns = router.urls


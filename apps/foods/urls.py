from rest_framework.routers import DefaultRouter

from .views import FoodManagementViewSet

router = DefaultRouter()
router.register(r'', FoodManagementViewSet, basename='food-management')

urlpatterns = router.urls


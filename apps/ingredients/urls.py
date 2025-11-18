from rest_framework.routers import DefaultRouter

from .views import IngredientManagementViewSet

router = DefaultRouter()
router.register(r'', IngredientManagementViewSet, basename='ingredient-management')

urlpatterns = router.urls

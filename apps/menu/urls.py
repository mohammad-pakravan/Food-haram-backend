from rest_framework.routers import DefaultRouter

from .views import MenuPlanViewSet

router = DefaultRouter()
router.register(r'', MenuPlanViewSet, basename='menu-plan')

urlpatterns = router.urls


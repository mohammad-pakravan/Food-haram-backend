from rest_framework.routers import DefaultRouter
from .views import DirectSaleViewSet

router = DefaultRouter()
router.register(r'', DirectSaleViewSet, basename='direct-sale')

urlpatterns = router.urls


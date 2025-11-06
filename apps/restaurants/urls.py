from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRestaurantPermissionViewSet

app_name = 'restaurants'

router = DefaultRouter()
router.register(r'permissions', UserRestaurantPermissionViewSet, basename='permission')

urlpatterns = [
    path('', include(router.urls)),
]


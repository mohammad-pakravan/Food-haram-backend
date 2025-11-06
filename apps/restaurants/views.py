from rest_framework import permissions, viewsets
from .models import UserRestaurantPermission
from .serializers import UserRestaurantPermissionSerializer


class UserRestaurantPermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing user-restaurant permissions (Read-only).
    
    Provides read-only operations for user-restaurant permissions.
    Filters permissions based on user access rights.
    """
    serializer_class = UserRestaurantPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for this endpoint
    
    def get_queryset(self):
        """
        Filter permissions based on user access rights.
        
        - Central users can see all permissions
        - Regular users can only see their own permission (one-to-one relationship)
        """
        user = self.request.user
        
        # Check if user is authenticated (for Swagger schema generation)
        if not user.is_authenticated:
            return UserRestaurantPermission.objects.none()
        
        if user.is_central:
            # Central users can see all permissions
            return UserRestaurantPermission.objects.all().select_related('user', 'restaurant')
        
        # Regular users can only see their own permission
        return UserRestaurantPermission.objects.filter(
            user=user
        ).select_related('user', 'restaurant')


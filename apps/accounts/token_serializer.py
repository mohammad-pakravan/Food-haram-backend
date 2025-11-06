from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import PermissionDenied


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with additional claims for panel-based access"""
    
    @classmethod
    def get_token(cls, user, active_role=None, restaurant_id=None):
        """Create token with custom claims"""
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = user.id
        token['username'] = user.username
        token['is_central'] = user.is_central
        
        # Add active role and restaurant if provided
        if active_role:
            token['active_role'] = active_role
        if restaurant_id:
            token['restaurant_id'] = restaurant_id
        
        # Add restaurant information if user has restaurant permission
        if not user.is_central:
            from apps.restaurants.models import UserRestaurantPermission
            try:
                permission = UserRestaurantPermission.objects.select_related('restaurant').get(user=user)
                if not restaurant_id:  # Only set if not already set
                    token['restaurant_id'] = permission.restaurant.id
                token['restaurant_name'] = permission.restaurant.name
            except UserRestaurantPermission.DoesNotExist:
                token['restaurant_id'] = None
                token['restaurant_name'] = None
        
        return token
    
    def validate(self, attrs):
        """Validate credentials and panel access"""
        data = super().validate(attrs)
        
        # Get panel from request data (required)
        request = self.context.get('request')
        panel = request.data.get('panel') if request else None
        
        # Panel is required
        if not panel:
            raise PermissionDenied("Panel (role) is required for login.")
        
        user = self.user
        active_role = None
        restaurant_id = None
        restaurant_data = None
        
        # Check if user has access to the specified panel
        if user.is_central:
            # Central users have access to all panels
            active_role = panel
            restaurant_data = None
        else:
            # Check if user has this role in their restaurant
            from apps.restaurants.models import UserRestaurantPermission
            try:
                permission = UserRestaurantPermission.objects.select_related('restaurant').get(user=user)
                
                # Ensure roles is a list
                user_roles = permission.roles if isinstance(permission.roles, list) else []
                
                # Check if panel (role) is in user's roles
                if panel not in user_roles:
                    raise PermissionDenied("You don't have permission to access this panel.")
                
                active_role = panel
                restaurant_id = permission.restaurant.id
                restaurant_data = {
                    'id': permission.restaurant.id,
                    'name': permission.restaurant.name
                }
            except UserRestaurantPermission.DoesNotExist:
                raise PermissionDenied("You don't have permission to access this panel.")
        
        # Regenerate token with active role and restaurant
        refresh = self.get_token(user, active_role=active_role, restaurant_id=restaurant_id)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add user information to response
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'active_role': active_role,
            'restaurant': restaurant_data
        }
        
        return data


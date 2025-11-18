from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import PermissionDenied


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with additional claims for panel-based access"""
    
    @classmethod
    def get_token(cls, user, active_role=None):
        """Create token with custom claims"""
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = user.id
        token['username'] = user.username
        token['is_central'] = user.is_central
        token['roles'] = user.get_roles()
        
        if active_role:
            token['active_role'] = active_role
        
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
        
        # Check if user has access to the specified panel
        if user.is_central:
            # Central users have access to all panels
            active_role = panel
        else:
            user_roles = user.get_roles()
            if panel not in user_roles:
                raise PermissionDenied("You don't have permission to access this panel.")
            active_role = panel
        
        # Regenerate token with active role
        refresh = self.get_token(user, active_role=active_role)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add user information to response
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'active_role': active_role,
            'roles': user.get_roles(),
            'is_central': user.is_central,
        }
        
        return data


from rest_framework.permissions import BasePermission


class HasPanelAccess(BasePermission):
    """
    Permission class to check if user has access to a specific panel.
    Subclass this and set required_role to use it in views.
    """
    required_role = None

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        # Central users always have access
        if user.is_central:
            return True
        
        if not self.required_role:
            return True
        
        # Check access in any restaurant
        if user.has_role(self.required_role):
            return True
        
        # If restaurant_id exists in request, check access in that restaurant
        restaurant_id = self.get_restaurant_id(request, view)
        if restaurant_id:
            return user.has_restaurant_access(restaurant_id, self.required_role)
        
        return False
    
    def get_restaurant_id(self, request, view):
        """Extract restaurant_id from request or view"""
        # From query params
        restaurant_id = request.query_params.get('restaurant_id') or request.data.get('restaurant_id')
        if restaurant_id:
            return int(restaurant_id)
        
        # From URL kwargs (for ViewSet with pk)
        if hasattr(view, 'kwargs') and 'restaurant_id' in view.kwargs:
            return int(view.kwargs['restaurant_id'])
        
        # From pk in ViewSet (if pk is related to Restaurant)
        if hasattr(view, 'kwargs') and 'pk' in view.kwargs:
            # Check if pk is related to Restaurant
            try:
                from apps.restaurants.models import Restaurant
                restaurant = Restaurant.objects.get(pk=view.kwargs['pk'])
                return restaurant.id
            except (Restaurant.DoesNotExist, ValueError):
                pass
        
        return None


class HasRestaurantAccess(BasePermission):
    """
    Permission class to check if user has access to a specific restaurant
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        # Central users always have access
        if user.is_central:
            return True
        
        restaurant_id = self.get_restaurant_id(request, view)
        if not restaurant_id:
            return False
        
        return user.has_restaurant_access(restaurant_id)
    
    def get_restaurant_id(self, request, view):
        """Extract restaurant_id from request or view"""
        restaurant_id = request.query_params.get('restaurant_id') or request.data.get('restaurant_id')
        if restaurant_id:
            return int(restaurant_id)
        
        if hasattr(view, 'kwargs') and 'restaurant_id' in view.kwargs:
            return int(view.kwargs['restaurant_id'])
        
        if hasattr(view, 'kwargs') and 'pk' in view.kwargs:
            try:
                from apps.restaurants.models import Restaurant
                restaurant = Restaurant.objects.get(pk=view.kwargs['pk'])
                return restaurant.id
            except (Restaurant.DoesNotExist, ValueError):
                pass
        
        return None


# Permission classes for each panel
class KitchenAccess(HasPanelAccess):
    required_role = 'kitchen_manager'


class RestaurantAccess(HasPanelAccess):
    required_role = 'restaurant_manager'


class TokenIssuerAccess(HasPanelAccess):
    required_role = 'token_issuer'


class DeliveryDeskAccess(HasPanelAccess):
    required_role = 'delivery_desk'


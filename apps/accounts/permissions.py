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
        
        return user.has_role(self.required_role)


# Permission classes for each panel
class KitchenAccess(HasPanelAccess):
    required_role = 'kitchen_manager'


class RestaurantAccess(HasPanelAccess):
    required_role = 'restaurant_manager'


class TokenIssuerAccess(HasPanelAccess):
    required_role = 'token_issuer'


class DeliveryDeskAccess(HasPanelAccess):
    required_role = 'delivery_desk'


class RestaurantOrKitchenAccess(BasePermission):
    """
    Permission class that allows both restaurant_manager and kitchen_manager roles.
    Central users always have access.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        # Central users always have access
        if user.is_central:
            return True
        
        # Allow restaurant_manager or kitchen_manager
        return user.has_role('restaurant_manager') or user.has_role('kitchen_manager')


from django.contrib.auth.models import AbstractUser
from django.db import models


class AccessRole(models.TextChoices):
    KITCHEN_MANAGER = 'kitchen_manager', 'مدیر آشپزخانه'
    RESTAURANT_MANAGER = 'restaurant_manager', 'مدیر رستوران'
    TOKEN_ISSUER = 'token_issuer', 'صدور ژتون'
    DELIVERY_DESK = 'delivery_desk', 'تحویل غذا'


class User(AbstractUser):
    """User model with support for central users"""
    is_central = models.BooleanField(
        default=False,
        verbose_name='کاربر مرکزی',
        help_text='کاربران مرکزی به تمام رستوران‌ها و دسترسی‌ها دسترسی دارند'
    )

    def has_role(self, role_name: str, restaurant_id: int = None) -> bool:
        """
        Check if user has access to a specific role.
        
        If restaurant_id is provided, checks only in that restaurant.
        If user is central, always returns True.
        
        Args:
            role_name: The role name to check
            restaurant_id: Optional restaurant ID to check in specific restaurant
            
        Returns:
            bool: True if user has the role, False otherwise
        """
        from apps.restaurants.models import UserRestaurantPermission
        
        if self.is_central:
            return True
        
        if restaurant_id:
            # Check access in specific restaurant
            return UserRestaurantPermission.objects.filter(
                user=self,
                restaurant_id=restaurant_id,
                roles__contains=[role_name]
            ).exists()
        
        # Check access in any restaurant
        return UserRestaurantPermission.objects.filter(
            user=self,
            roles__contains=[role_name]
        ).exists()

    def has_restaurant_access(self, restaurant_id: int, role_name: str = None) -> bool:
        """
        Check if user has access to a specific restaurant.
        
        If role_name is provided, checks if user has that role in the restaurant.
        
        Args:
            restaurant_id: The restaurant ID to check
            role_name: Optional role name to check
            
        Returns:
            bool: True if user has access, False otherwise
        """
        from apps.restaurants.models import UserRestaurantPermission
        
        if self.is_central:
            return True
        
        query = UserRestaurantPermission.objects.filter(
            user=self,
            restaurant_id=restaurant_id
        )
        
        if role_name:
            query = query.filter(roles__contains=[role_name])
        
        return query.exists()

    def get_restaurant_permissions(self, restaurant_id: int) -> list:
        """
        Get list of user roles in a specific restaurant.
        
        Args:
            restaurant_id: The restaurant ID
            
        Returns:
            list: List of role names
        """
        from apps.restaurants.models import UserRestaurantPermission
        
        if self.is_central:
            return [role[0] for role in AccessRole.choices]
        
        try:
            permission = UserRestaurantPermission.objects.get(
                user=self,
                restaurant_id=restaurant_id
            )
            return permission.roles if permission.roles else []
        except UserRestaurantPermission.DoesNotExist:
            return []

    def get_restaurant(self):
        """
        Get user's restaurant (each user can only have one restaurant).
        
        Returns:
            Restaurant: User's restaurant or None if central user or no restaurant
        """
        from apps.restaurants.models import UserRestaurantPermission
        
        if self.is_central:
            # Central users don't have a specific restaurant
            return None
        
        try:
            permission = UserRestaurantPermission.objects.get(user=self)
            return permission.restaurant if permission.restaurant.is_active else None
        except UserRestaurantPermission.DoesNotExist:
            return None
    
    def get_restaurants(self):
        """
        Get list of restaurants user has access to (for backward compatibility).
        
        Returns:
            list: List of Restaurant objects
        """
        restaurant = self.get_restaurant()
        if restaurant:
            return [restaurant]
        return []

    def __str__(self):
        central_status = " (Central)" if self.is_central else ""
        return f"{self.username}{central_status}"


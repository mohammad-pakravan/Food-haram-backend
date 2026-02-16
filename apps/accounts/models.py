from django.contrib.auth.models import AbstractUser
from django.db import models


class AccessRole(models.TextChoices):
    KITCHEN_MANAGER = 'kitchen_manager', 'مدیر آشپزخانه'
    RESTAURANT_MANAGER = 'restaurant_manager', 'مدیر رستوران'
    TOKEN_ISSUER = 'token_issuer', 'صدور ژتون'
    DELIVERY_DESK = 'delivery_desk', 'تحویل غذا'
    WAREHOUSE_MANAGER = 'warehouse_manager', 'انباردار'


class User(AbstractUser):
    """User model with support for central users"""
    is_central = models.BooleanField(
        default=False,
        verbose_name='کاربر مرکزی',
        help_text='کاربران مرکزی به تمام دسترسی‌ها دسترسی دارند'
    )
    roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name='نقش‌ها',
        help_text='لیست نقش‌های دسترسی کاربر'
    )

    def get_roles(self) -> list:
        """
        Return list of roles assigned to the user.
        Central users implicitly have access to all roles.
        """
        if self.is_central:
            return [role[0] for role in AccessRole.choices]
        if isinstance(self.roles, list):
            return self.roles
        return []

    def has_role(self, role_name: str) -> bool:
        """Check if user has the specified role (central users pass automatically)."""
        if self.is_central:
            return True
        return role_name in self.get_roles()

    def __str__(self):
        central_status = " (Central)" if self.is_central else ""
        return f"{self.username}{central_status}"


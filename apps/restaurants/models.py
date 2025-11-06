from django.db import models
from django.core.validators import MinLengthValidator
from apps.accounts.models import User, AccessRole


class Center(models.Model):
    """Center model for grouping restaurants"""
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='نام مرکز',
        validators=[MinLengthValidator(2)]
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='آدرس'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='تلفن'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )

    class Meta:
        verbose_name = 'مرکز'
        verbose_name_plural = 'مراکز'
        ordering = ['name']

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    """Restaurant model for managing different restaurants"""
    center = models.ForeignKey(
        Center,
        on_delete=models.CASCADE,
        related_name='restaurants',
        verbose_name='مرکز',
        help_text='مرکز مربوط به این رستوران'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='نام رستوران',
        validators=[MinLengthValidator(2)]
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='آدرس'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='تلفن'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )

    class Meta:
        verbose_name = 'رستوران'
        verbose_name_plural = 'رستوران‌ها'
        ordering = ['center', 'name']
        unique_together = ['center', 'name']

    def __str__(self):
        return f"{self.center.name} - {self.name}"


class UserRestaurantPermission(models.Model):
    """User-Restaurant permission model with access roles"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='restaurant_permission',
        verbose_name='کاربر',
        help_text='هر کاربر فقط می‌تواند به یک رستوران متصل باشد'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='user_permissions',
        verbose_name='رستوران'
    )
    roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name='نقش‌های دسترسی',
        help_text='لیست نقش‌های دسترسی کاربر در این رستوران'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )

    class Meta:
        verbose_name = 'دسترسی کاربر به رستوران'
        verbose_name_plural = 'ارتباط کاربران - رستوران'
        ordering = ['-created_at']

    def __str__(self):
        roles_str = ', '.join(self.roles) if self.roles else 'No roles'
        return f"{self.user.username} - {self.restaurant.name} ({roles_str})"


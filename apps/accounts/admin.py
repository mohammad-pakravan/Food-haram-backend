from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_central', 'get_restaurants_count', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'is_central']
    search_fields = ['username', 'email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('is_central',)
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('is_central',)
        }),
    )
    
    def get_restaurants_count(self, obj):
        """Display count of user's restaurants"""
        from apps.restaurants.models import UserRestaurantPermission
        
        if obj.is_central:
            return "All (Central)"
        count = UserRestaurantPermission.objects.filter(user=obj).count()
        return count
    get_restaurants_count.short_description = 'تعداد رستوران‌ها'

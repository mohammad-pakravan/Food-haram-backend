from django.contrib import admin
from django import forms
from .models import Center, Restaurant, UserRestaurantPermission
from apps.accounts.models import AccessRole


class RestaurantInline(admin.TabularInline):
    """Inline for managing restaurants in center page"""
    model = Restaurant
    extra = 1
    fields = ('name', 'description', 'phone', 'address', 'is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    verbose_name = 'رستوران'
    verbose_name_plural = 'رستوران‌ها'


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'address', 'get_restaurants_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RestaurantInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('اطلاعات تماس', {
            'fields': ('phone', 'address')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_restaurants_count(self, obj):
        """Display count of restaurants in the center"""
        count = Restaurant.objects.filter(center=obj, is_active=True).count()
        return count
    get_restaurants_count.short_description = 'تعداد رستوران‌ها'


class UserRestaurantPermissionForm(forms.ModelForm):
    """Form for selecting roles from dropdown"""
    roles = forms.MultipleChoiceField(
        choices=AccessRole.choices,
        widget=forms.SelectMultiple(attrs={'size': len(AccessRole.choices)}),
        required=False,
        help_text='نقش‌های دسترسی کاربر در این رستوران را انتخاب کنید'
    )
    
    class Meta:
        model = UserRestaurantPermission
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # If instance exists, show current roles as selected
            self.fields['roles'].initial = self.instance.roles
        else:
            self.fields['roles'].initial = []
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert selections to list
        instance.roles = list(self.cleaned_data.get('roles', []))
        if commit:
            instance.save()
        return instance


class UserRestaurantPermissionInline(admin.TabularInline):
    """Inline for managing users and permissions in restaurant page"""
    model = UserRestaurantPermission
    form = UserRestaurantPermissionForm
    extra = 1
    fields = ('user', 'roles', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['user']
    verbose_name = 'کاربر و دسترسی'
    verbose_name_plural = 'کاربران و دسترسی‌ها'
    
    def get_queryset(self, request):
        """Optimize query for better display"""
        qs = super().get_queryset(request)
        return qs.select_related('user').order_by('-created_at')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'center', 'phone', 'address', 'get_users_count', 'is_active', 'created_at']
    list_filter = ['center', 'is_active', 'created_at']
    search_fields = ['name', 'center__name', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['center']
    inlines = [UserRestaurantPermissionInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('center', 'name', 'description', 'is_active')
        }),
        ('اطلاعات تماس', {
            'fields': ('phone', 'address')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_users_count(self, obj):
        """Display count of users in the restaurant"""
        count = UserRestaurantPermission.objects.filter(restaurant=obj).count()
        return count
    get_users_count.short_description = 'تعداد کاربران'


@admin.register(UserRestaurantPermission)
class UserRestaurantPermissionAdmin(admin.ModelAdmin):
    form = UserRestaurantPermissionForm
    list_display = ['user', 'restaurant', 'get_roles_display', 'created_at']
    list_filter = ['restaurant', 'created_at']
    search_fields = ['user__username', 'restaurant__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user', 'restaurant']
    
    def get_roles_display(self, obj):
        if not obj.roles:
            return 'No roles'
        role_names = [dict(AccessRole.choices).get(role, role) for role in obj.roles]
        return ', '.join(role_names)
    get_roles_display.short_description = 'نقش‌ها'


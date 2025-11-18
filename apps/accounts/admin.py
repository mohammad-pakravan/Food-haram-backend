from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User, AccessRole


class UserAdminCreationForm(UserCreationForm):
    roles = forms.MultipleChoiceField(
        choices=AccessRole.choices,
        required=False,
        widget=forms.SelectMultiple(attrs={'size': len(AccessRole.choices)}),
        label='نقش‌ها'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'is_central', 'roles')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.roles = list(self.cleaned_data.get('roles', []))
        if commit:
            user.save()
        return user


class UserAdminChangeForm(UserChangeForm):
    roles = forms.MultipleChoiceField(
        choices=AccessRole.choices,
        required=False,
        widget=forms.SelectMultiple(attrs={'size': len(AccessRole.choices)}),
        label='نقش‌ها'
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and isinstance(self.instance.roles, list):
            self.fields['roles'].initial = self.instance.roles

    def save(self, commit=True):
        user = super().save(commit=False)
        user.roles = list(self.cleaned_data.get('roles', []))
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    list_display = ['username', 'email', 'is_central', 'display_roles', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'is_central']
    search_fields = ['username', 'email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('is_central', 'roles')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('اطلاعات اضافی', {
            'fields': ('is_central', 'roles')
        }),
    )

    def display_roles(self, obj):
        roles = obj.get_roles()
        if not roles:
            return '-'
        return ', '.join(roles)

    display_roles.short_description = 'نقش‌ها'

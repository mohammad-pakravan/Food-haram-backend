from django.contrib import admin

from .models import MenuPlan


@admin.register(MenuPlan)
class MenuPlanAdmin(admin.ModelAdmin):
    list_display = ('date', 'food', 'meal_type', 'capacity', 'cook_status')
    list_filter = ('meal_type', 'cook_status', 'date')
    search_fields = ('food__title',)
    autocomplete_fields = ('food', 'dessert')
    ordering = ('-date', 'meal_type')
    readonly_fields = ('created_at', 'updated_at')

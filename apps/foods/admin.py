from django.contrib import admin

from .models import Food, Dessert, FoodIngredient


class FoodIngredientInline(admin.TabularInline):
    model = FoodIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'amount_per_serving')


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'meal_type', 'preparation_time', 'unit_price')
    list_filter = ('category', 'meal_type')
    search_fields = ('title',)
    ordering = ('title',)
    inlines = (FoodIngredientInline,)
    readonly_fields: tuple = ()


@admin.register(Dessert)
class DessertAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'unit_price', 'updated_at')
    list_filter = ('category',)
    search_fields = ('title',)
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')

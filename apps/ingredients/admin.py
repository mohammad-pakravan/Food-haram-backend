from django.contrib import admin

from .models import Ingredient, InventoryStock, InventoryLog


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'unit_price', 'warning_amount', 'created_at', 'updated_at')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InventoryStock)
class InventoryStockAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'total_amount', 'last_received_date', 'created_at', 'updated_at')
    search_fields = ('ingredient__name',)
    autocomplete_fields = ('ingredient',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'amount', 'unit', 'code', 'date', 'created_at')
    list_filter = ('unit',)
    search_fields = ('inventory__ingredient__name', 'code')
    autocomplete_fields = ('inventory',)
    readonly_fields = ('created_at', 'updated_at')

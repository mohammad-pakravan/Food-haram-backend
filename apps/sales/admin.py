from django.contrib import admin

from .models import DirectSale, DirectSaleItem


class DirectSaleItemInline(admin.TabularInline):
    model = DirectSaleItem
    extra = 1
    autocomplete_fields = ('food',)
    fields = ('food', 'count')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DirectSale)
class DirectSaleAdmin(admin.ModelAdmin):
    list_display = ('sale_code', 'customer_name', 'date', 'total_price', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('sale_code', 'customer_name', 'phone')
    inlines = (DirectSaleItemInline,)
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DirectSaleItem)
class DirectSaleItemAdmin(admin.ModelAdmin):
    list_display = ('direct_sale', 'food', 'count', 'created_at')
    search_fields = ('direct_sale__customer_name', 'food__title')
    autocomplete_fields = ('direct_sale', 'food')
    readonly_fields = ('created_at', 'updated_at')

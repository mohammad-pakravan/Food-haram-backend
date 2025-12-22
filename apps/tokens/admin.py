from django.contrib import admin

from .models import Token, TokenItem


class TokenItemInline(admin.TabularInline):
    model = TokenItem
    extra = 1
    autocomplete_fields = ('food',)
    fields = ('food', 'count')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('token_code', 'customer_name', 'date', 'total_price', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('token_code', 'customer_name', 'phone')
    inlines = (TokenItemInline,)
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TokenItem)
class TokenItemAdmin(admin.ModelAdmin):
    list_display = ('token', 'food', 'count', 'created_at')
    search_fields = ('token__token_code', 'food__title')
    autocomplete_fields = ('token', 'food')
    readonly_fields = ('created_at', 'updated_at')

from rest_framework import serializers
from datetime import date
import jdatetime
from .models import InventoryStock, InventoryLog, Ingredient


class JalaliDateField(serializers.Field):
    """
    Custom field for Jalali (Persian) date conversion.
    Accepts Jalali date string (YYYY-MM-DD) and converts to Gregorian date.
    Returns Jalali date string when serializing.
    """
    
    def to_representation(self, value):
        """Convert Gregorian date to Jalali string"""
        if value is None:
            return None
        if isinstance(value, date):
            jalali = jdatetime.date.fromgregorian(date=value)
            return jalali.strftime('%Y-%m-%d')
        return value
    
    def to_internal_value(self, data):
        """Convert Jalali date string to Gregorian date"""
        if not data:
            return None
        try:
            # Parse Jalali date string (YYYY-MM-DD)
            year, month, day = map(int, data.split('-'))
            jalali_date = jdatetime.date(year, month, day)
            gregorian_date = jalali_date.togregorian()
            return gregorian_date
        except (ValueError, AttributeError) as e:
            raise serializers.ValidationError(f'فرمت تاریخ شمسی نامعتبر است. فرمت صحیح: YYYY-MM-DD (مثال: 1403-08-28)')


class InventoryStockSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_category = serializers.SerializerMethodField()
    ingredient_subcategory = serializers.SerializerMethodField()
    ingredient_unit = serializers.CharField(source='ingredient.unit', read_only=True)
    warning_amount = serializers.IntegerField(source='ingredient.warning_amount', read_only=True)
    is_low_stock = serializers.SerializerMethodField()
    last_received_date = JalaliDateField(required=False)

    class Meta:
        model = InventoryStock
        fields = [
            'id',
            'ingredient',
            'ingredient_name',
            'ingredient_category',
            'ingredient_subcategory',
            'ingredient_unit',
            'total_amount',
            'warning_amount',
            'is_low_stock',
            'last_received_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ingredient_name', 'ingredient_category', 'ingredient_subcategory', 'ingredient_unit', 'warning_amount', 'is_low_stock']

    def get_ingredient_category(self, obj):
        """Return Persian label for ingredient category"""
        from .models import CATEGORY_TYPE_CHOICES
        category_dict = dict(CATEGORY_TYPE_CHOICES)
        return category_dict.get(obj.ingredient.category, obj.ingredient.category)

    def get_ingredient_subcategory(self, obj):
        """Return Persian label for ingredient subcategory"""
        from .models import SUBCATEGORY_CHOICES
        subcategory_dict = dict(SUBCATEGORY_CHOICES)
        return subcategory_dict.get(obj.ingredient.subcategory, obj.ingredient.subcategory)

    def get_is_low_stock(self, obj):
        """Check if stock is below warning amount"""
        return obj.total_amount <= obj.ingredient.warning_amount


class InventoryLogSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='inventory.ingredient.name', read_only=True)
    ingredient_id = serializers.IntegerField(source='inventory.ingredient.id', read_only=True)
    date = JalaliDateField(required=True)

    class Meta:
        model = InventoryLog
        fields = [
            'id',
            'inventory',
            'ingredient_id',
            'ingredient_name',
            'amount',
            'unit',
            'code',
            'date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ingredient_name', 'ingredient_id']



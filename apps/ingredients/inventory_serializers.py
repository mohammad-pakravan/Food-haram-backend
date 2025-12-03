from rest_framework import serializers
from .models import InventoryStock, InventoryLog, Ingredient


class InventoryStockSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_category = serializers.CharField(source='ingredient.category', read_only=True)
    ingredient_unit = serializers.CharField(source='ingredient.unit', read_only=True)
    warning_amount = serializers.IntegerField(source='ingredient.warning_amount', read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventoryStock
        fields = [
            'id',
            'ingredient',
            'ingredient_name',
            'ingredient_category',
            'ingredient_unit',
            'total_amount',
            'warning_amount',
            'is_low_stock',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ingredient_name', 'ingredient_category', 'ingredient_unit', 'warning_amount', 'is_low_stock']

    def get_is_low_stock(self, obj):
        """Check if stock is below warning amount"""
        return obj.total_amount <= obj.ingredient.warning_amount


class InventoryLogSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='inventory.ingredient.name', read_only=True)
    ingredient_id = serializers.IntegerField(source='inventory.ingredient.id', read_only=True)

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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ingredient_name', 'ingredient_id']


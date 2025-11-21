from rest_framework import serializers

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'category',
            'unit',
            'unit_price',
            'code',
            'warning_amount',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

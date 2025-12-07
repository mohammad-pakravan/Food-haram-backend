from rest_framework import serializers

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    category_value = serializers.CharField(source='category', write_only=True, required=False)
    subcategory_value = serializers.CharField(source='subcategory', write_only=True, required=False)

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'category',
            'subcategory',
            'category_value',
            'subcategory_value',
            'unit',
            'unit_price',
            'code',
            'warning_amount',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'category', 'subcategory')

    def get_category(self, obj):
        """Return Persian label for category"""
        from .models import CATEGORY_TYPE_CHOICES
        category_dict = dict(CATEGORY_TYPE_CHOICES)
        return category_dict.get(obj.category, obj.category)

    def get_subcategory(self, obj):
        """Return Persian label for subcategory"""
        from .models import SUBCATEGORY_CHOICES
        subcategory_dict = dict(SUBCATEGORY_CHOICES)
        return subcategory_dict.get(obj.subcategory, obj.subcategory)

    def validate(self, attrs):
        # Handle category_value and subcategory_value for input
        if 'category_value' in attrs:
            attrs['category'] = attrs.pop('category_value')
        if 'subcategory_value' in attrs:
            attrs['subcategory'] = attrs.pop('subcategory_value')
        
        category = attrs.get('category')
        subcategory = attrs.get('subcategory')
        
        # If updating, get existing values if not provided
        if self.instance:
            if category is None:
                category = self.instance.category
            if subcategory is None:
                subcategory = self.instance.subcategory
        
        # Validate subcategory matches category
        if category and subcategory:
            from .models import CATEGORY_SUBCATEGORY_MAP, CATEGORY_TYPE_CHOICES
            valid_subcategories = CATEGORY_SUBCATEGORY_MAP.get(category, [])
            if subcategory not in valid_subcategories:
                category_dict = dict(CATEGORY_TYPE_CHOICES)
                category_label = category_dict.get(category, category)
                raise serializers.ValidationError({
                    'subcategory_value': f'زیر دسته‌بندی انتخاب شده با دسته‌بندی {category_label} مطابقت ندارد.'
                })
        
        return attrs

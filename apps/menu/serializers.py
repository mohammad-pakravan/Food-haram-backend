from rest_framework import serializers
from datetime import date
import jdatetime
from decimal import Decimal

from .models import MenuPlan


class JalaliDateField(serializers.Field):
    """
    Custom field for Jalali (Persian) date conversion.
    Accepts Jalali date string (YYYY-MM-DD) and converts to Gregorian date.
    Returns Jalali date string when serializing.
    """
    
    def to_representation(self, value):
        """Convert Gregorian date or jdatetime.date to Jalali string"""
        if value is None:
            return None
        # Handle jdatetime.date objects (from django-jalali)
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            try:
                # Check if it's already a jdatetime.date
                if hasattr(value, 'togregorian'):
                    # It's a jdatetime.date, use it directly
                    return value.strftime('%Y-%m-%d')
                else:
                    # It's a regular date, convert to jalali
                    jalali = jdatetime.date.fromgregorian(date=value)
                    return jalali.strftime('%Y-%m-%d')
            except (AttributeError, ValueError):
                pass
        return str(value) if value else None
    
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


class MenuPlanSerializer(serializers.ModelSerializer):
    food_title = serializers.CharField(source='food.title', read_only=True)
    food_category = serializers.CharField(source='food.category', read_only=True)
    food_preparation_time = serializers.IntegerField(source='food.preparation_time', read_only=True)
    dessert_title = serializers.CharField(source='dessert.title', read_only=True, allow_null=True)
    date_jalali = JalaliDateField(source='date', required=False)
    required_ingredients = serializers.SerializerMethodField()

    class Meta:
        model = MenuPlan
        fields = [
            'id',
            'date_jalali',
            'food',
            'food_title',
            'food_category',
            'food_preparation_time',
            'meal_type',
            'capacity',
            'dessert',
            'dessert_title',
            'dessert_count',
            'cook_status',
            'required_ingredients',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'food_title', 'food_category', 'food_preparation_time', 'dessert_title', 'required_ingredients']

    # cook_status is now editable by kitchen managers

    def get_required_ingredients(self, obj):
        """
        محاسبه مواد اولیه مورد نیاز برای این برنامه غذایی
        مقدار مورد نیاز = amount_per_serving × capacity
        """
        if not obj.food:
            return []
        
        ingredients_data = []
        food_ingredients = obj.food.ingredients.all()
        
        for food_ingredient in food_ingredients:
            # محاسبه مقدار مورد نیاز: مقدار برای هر سرو × ظرفیت
            required_amount = Decimal(str(food_ingredient.amount_per_serving)) * Decimal(str(obj.capacity))
            
            ingredients_data.append({
                'ingredient_id': food_ingredient.ingredient.id,
                'ingredient_name': food_ingredient.ingredient.name,
                'ingredient_code': food_ingredient.ingredient.code,
                'ingredient_unit': food_ingredient.ingredient.unit,
                'amount_per_serving': str(food_ingredient.amount_per_serving),
                'capacity': obj.capacity,
                'required_amount': str(required_amount),
            })
        
        return ingredients_data

    def validate(self, attrs):
        """Ensure date is provided and convert date_jalali to date"""
        initial_data = getattr(self, 'initial_data', {})
        
        # Handle date_jalali input - convert to date
        if 'date_jalali' in initial_data:
            jalali_field = JalaliDateField()
            try:
                gregorian_date = jalali_field.to_internal_value(initial_data['date_jalali'])
                attrs['date'] = gregorian_date
            except serializers.ValidationError as e:
                raise serializers.ValidationError({'date_jalali': str(e)})
        
        # Check if date is provided (either directly or via date_jalali)
        if 'date' not in attrs and not self.instance:
                raise serializers.ValidationError({'date_jalali': 'تاریخ الزامی است.'})
        
        # Ensure cook_status defaults to 'pending' if not provided
        if 'cook_status' not in attrs and not self.instance:
            attrs['cook_status'] = 'pending'
        
        return attrs


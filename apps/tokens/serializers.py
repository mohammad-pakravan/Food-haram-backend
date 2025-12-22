from rest_framework import serializers
from datetime import date
import jdatetime
import secrets
import string
from drf_yasg.utils import swagger_serializer_method
from drf_yasg import openapi

from .models import Token, TokenItem
from apps.foods.models import Food


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


class FoodItemSerializer(serializers.Serializer):
    """Serializer for food items in token creation"""
    food = serializers.PrimaryKeyRelatedField(queryset=Food.objects.all())
    count = serializers.IntegerField(min_value=1)


class TokenItemReadSerializer(serializers.ModelSerializer):
    """Serializer for reading TokenItem"""
    food_title = serializers.CharField(source='food.title', read_only=True)
    food_unit_price = serializers.DecimalField(source='food.unit_price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = TokenItem
        fields = ['id', 'food', 'food_title', 'food_unit_price', 'count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TokenCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Token with TokenItems"""
    date = JalaliDateField()
    category = serializers.ChoiceField(
        choices=[('normal', 'عادی'), ('hazrati', 'حضرتی')],
        write_only=True
    )
    foods = FoodItemSerializer(many=True, required=False)
    token_code = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Token
        fields = [
            'id',
            'token_code',
            'date',
            'category',
            'customer_name',
            'phone',
            'foods',
            'items',
            'total_price',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'token_code', 'total_price', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Remove foods from representation"""
        ret = super().to_representation(instance)
        ret.pop('foods', None)
        return ret
    
    
    def validate_foods(self, value):
        """Validate that at least one food item is provided"""
        if not value or len(value) == 0:
            raise serializers.ValidationError('حداقل یک غذا باید انتخاب شود.')
        return value
    
    def validate(self, attrs):
        """Validate that all foods match the category"""
        category = attrs.get('category')
        # Get foods from attrs - it should be there after field validation
        foods_data = attrs.get('foods')
        
        # If foods is not in attrs (for update operations), try to get from initial_data
        if foods_data is None:
            initial_data = getattr(self, 'initial_data', {})
            foods_data = initial_data.get('foods')
        
        if category and foods_data:
            # Validate foods if they exist
            if isinstance(foods_data, list) and len(foods_data) > 0:
                # Validate each food item
                for food_item in foods_data:
                    # food_item should be a dict with 'food' and 'count'
                    if isinstance(food_item, dict):
                        food = food_item.get('food')
                    else:
                        food = food_item
                    
                    if food and hasattr(food, 'category'):
                        if food.category != category:
                            category_dict = dict([('normal', 'عادی'), ('hazrati', 'حضرتی')])
                            food_category_label = category_dict.get(food.category, food.category)
                            selected_category_label = category_dict.get(category, category)
                            raise serializers.ValidationError({
                                'foods': f'غذای "{food.title}" از دسته‌بندی {food_category_label} است اما دسته‌بندی انتخاب شده {selected_category_label} است.'
                            })
        
        # Always store foods in attrs so it's available in create/update
        # Even if it's None, we need to explicitly set it
        attrs['foods'] = foods_data
        
        return attrs
    
    @swagger_serializer_method(serializer_or_field=TokenItemReadSerializer(many=True))
    def get_items(self, obj):
        """Get token items"""
        items = obj.items.all()
        return TokenItemReadSerializer(items, many=True).data
    
    def generate_token_code(self):
        """Generate a random token code"""
        # Generate 8-character alphanumeric code
        alphabet = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        # Check if code already exists, regenerate if needed
        while Token.objects.filter(token_code=code).exists():
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        return code
    
    def create(self, validated_data):
        """Create Token and TokenItems together"""
        foods_data = validated_data.pop('foods')
        category = validated_data.pop('category')  # We don't store category in Token model
        
        # Generate token code
        token_code = self.generate_token_code()
        
        # Create Token
        token = Token.objects.create(
            token_code=token_code,
            **validated_data
        )
        
        # Calculate total price and create TokenItems
        total_price = 0
        for food_item in foods_data:
            food = food_item['food']
            count = food_item['count']
            
            # Calculate price for this item
            item_price = food.unit_price * count
            total_price += item_price
            
            # Create TokenItem
            TokenItem.objects.create(
                token=token,
                food=food,
                count=count
            )
        
        # Update total price
        token.total_price = total_price
        token.save()
        
        return token
    


class TokenListSerializer(serializers.ModelSerializer):
    """Serializer for listing tokens"""
    date = JalaliDateField()
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Token
        fields = [
            'id',
            'token_code',
            'date',
            'customer_name',
            'phone',
            'total_price',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'token_code', 'total_price', 'items', 'created_at', 'updated_at']
    
    @swagger_serializer_method(serializer_or_field=TokenItemReadSerializer(many=True))
    def get_items(self, obj):
        """Get token items"""
        items = obj.items.all()
        return TokenItemReadSerializer(items, many=True).data


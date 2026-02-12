from rest_framework import serializers
from datetime import date
import jdatetime
import secrets
import string
from django.db import transaction
from drf_yasg.utils import swagger_serializer_method
from drf_yasg import openapi

from .models import Token, TokenItem, STATUS_CHOICES
from apps.foods.models import Food, MEAL_TYPE_CHOICES
from apps.ingredients.models import HAZRATI_SUBCATEGORY_CHOICES, SUBCATEGORY_CHOICES
from apps.menu.models import MenuPlan


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
    class Meta:
        ref_name = 'TokenFoodItem'
    
    food = serializers.PrimaryKeyRelatedField(queryset=Food.objects.all())
    count = serializers.IntegerField(min_value=1)
    meal_type = serializers.ChoiceField(
        choices=[('breakfast', 'صبحانه'), ('lunch', 'ناهار'), ('dinner', 'شام')],
        required=False,
        allow_null=True,
        help_text='وعده غذایی (در صورت وجود چند وعده برای غذا، این فیلد الزامی است)'
    )


class TokenItemReadSerializer(serializers.ModelSerializer):
    """Serializer for reading TokenItem"""
    food_title = serializers.CharField(source='food.title', read_only=True)
    food_unit_price = serializers.DecimalField(source='food.unit_price', max_digits=10, decimal_places=2, read_only=True)
    meal_type_label = serializers.CharField(source='get_meal_type_display', read_only=True)
    
    class Meta:
        model = TokenItem
        fields = ['id', 'food', 'food_title', 'food_unit_price', 'meal_type', 'meal_type_label', 'count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'meal_type_label', 'created_at', 'updated_at']


class TokenCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Token with TokenItems"""
    date = JalaliDateField()
    subcategory = serializers.ChoiceField(
        choices=HAZRATI_SUBCATEGORY_CHOICES,
        write_only=True,
        help_text='زیر دسته‌بندی (همه توکن‌ها به صورت پیش‌فرض حضرتی هستند)'
    )
    foods = FoodItemSerializer(many=True, required=False)
    token_code = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items = serializers.SerializerMethodField()
    barcode_image_url = serializers.SerializerMethodField()
    qrcode_image_url = serializers.SerializerMethodField()
    class Meta:
        model = Token
        fields = [
            'id',
            'token_code',
            'date',
            'subcategory',
            'customer_name',
            'phone',
            'foods',
            'items',
            'barcode_image_url',
            'qrcode_image_url',
            'total_price',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'token_code', 'total_price', 'items',
            'barcode_image_url', 'qrcode_image_url',
            'created_at', 'updated_at'
        ]
    def get_barcode_image_url(self, obj):
        if obj.barcode_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.barcode_image.url) if request else obj.barcode_image.url
        return None

    def get_qrcode_image_url(self, obj):
        if obj.qrcode_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.qrcode_image.url) if request else obj.qrcode_image.url
        return None
    
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
        """Validate that all foods match the subcategory (all tokens are hazrati by default)"""
        subcategory = attrs.get('subcategory')
        # Get foods from attrs - it should be there after field validation
        foods_data = attrs.get('foods')
        
        # If foods is not in attrs, try to get from initial_data
        if foods_data is None:
            initial_data = getattr(self, 'initial_data', {})
            foods_data = initial_data.get('foods')
        
        # All tokens are hazrati by default, so category is always 'hazrati'
        category = 'hazrati'
        
        if subcategory and foods_data:
            # Validate foods if they exist
            if isinstance(foods_data, list) and len(foods_data) > 0:
                # Validate each food item
                for food_item in foods_data:
                    # food_item should be a dict with 'food' and 'count'
                    if isinstance(food_item, dict):
                        food = food_item.get('food')
                    else:
                        food = food_item
                    
                    if food and hasattr(food, 'category') and hasattr(food, 'subcategory'):
                        # Check category (must be hazrati)
                        if food.category != category:
                            raise serializers.ValidationError({
                                'foods': f'غذای "{food.title}" از دسته‌بندی عادی است. همه توکن‌ها باید از دسته‌بندی حضرتی باشند.'
                            })
                        
                        # Check subcategory match
                        if food.subcategory != subcategory:
                            subcategory_dict = dict(SUBCATEGORY_CHOICES)
                            food_subcategory_label = subcategory_dict.get(food.subcategory, food.subcategory)
                            selected_subcategory_label = subcategory_dict.get(subcategory, subcategory)
                            raise serializers.ValidationError({
                                'foods': f'غذای "{food.title}" از زیر دسته‌بندی {food_subcategory_label} است اما زیر دسته‌بندی انتخاب شده {selected_subcategory_label} است.'
                            })
        
        # Always store foods in attrs so it's available in create
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
    
    @transaction.atomic
    def create(self, validated_data):
        """Create Token and TokenItems together, and decrease MenuPlan capacity"""
        foods_data = validated_data.pop('foods')
        subcategory = validated_data.pop('subcategory')  # We don't store subcategory in Token model
        
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
            meal_type = food_item.get('meal_type')
            
            # Determine meal_type to use
            if meal_type is None:
                # If meal_type not specified, check if food has only one meal_type
                if not food.meal_types or len(food.meal_types) == 0:
                    raise serializers.ValidationError({
                        'foods': f'غذای "{food.title}" هیچ وعده غذایی تعریف نشده است.'
                    })
                elif len(food.meal_types) == 1:
                    # Use the single meal_type
                    meal_type = food.meal_types[0]
                else:
                    # Food has multiple meal_types, meal_type must be specified
                    raise serializers.ValidationError({
                        'foods': f'غذای "{food.title}" برای چند وعده تعریف شده است. لطفاً وعده مورد نظر را مشخص کنید (meal_type).'
                    })
            else:
                # Validate that the specified meal_type is valid for this food
                if meal_type not in food.meal_types:
                    meal_type_dict = dict(MEAL_TYPE_CHOICES)
                    valid_meal_types = [meal_type_dict.get(mt, mt) for mt in food.meal_types]
                    raise serializers.ValidationError({
                        'foods': f'وعده غذایی "{meal_type_dict.get(meal_type, meal_type)}" برای غذای "{food.title}" معتبر نیست. وعده‌های معتبر: {", ".join(valid_meal_types)}'
                    })
            
            # Calculate price for this item
            item_price = food.unit_price * count
            total_price += item_price
            
            # Decrease MenuPlan capacity first (before creating TokenItem)
            # Find MenuPlan with matching food, date, and meal_type
            menu_plan = MenuPlan.objects.filter(
                food=food,
                date=token.date,
                meal_type=meal_type
            ).first()
            
            if menu_plan:
                # Check if there's enough capacity
                if menu_plan.capacity < count:
                    raise serializers.ValidationError({
                        'foods': f'ظرفیت کافی برای غذای "{food.title}" در وعده {menu_plan.get_meal_type_display()} وجود ندارد. ظرفیت موجود: {menu_plan.capacity}، درخواستی: {count}'
                    })
                
                # Decrease capacity
                menu_plan.capacity -= count
                menu_plan.save()
            else:
                # If no MenuPlan found, raise an error
                meal_type_dict = dict(MEAL_TYPE_CHOICES)
                raise serializers.ValidationError({
                    'foods': f'برنامه غذایی برای غذای "{food.title}" در تاریخ {token.date} و وعده {meal_type_dict.get(meal_type, meal_type)} یافت نشد.'
                })
            
            # Create TokenItem after capacity check
            TokenItem.objects.create(
                token=token,
                food=food,
                meal_type=meal_type,
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
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    barcode_image_url = serializers.SerializerMethodField()
    qrcode_image_url = serializers.SerializerMethodField()
      
    class Meta:
        model = Token
        fields = [
            'id',
            'token_code',
            'date',
            'customer_name',
            'phone',
            'total_price',
            'status',
            'status_label',
            'items',
            'barcode_image_url',
            'qrcode_image_url',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id', 'token_code', 'total_price', 'status', 
            'status_label', 'items', 'barcode_image_url', 'qrcode_image_url',
            'created_at', 'updated_at'
        ]    
    @swagger_serializer_method(serializer_or_field=TokenItemReadSerializer(many=True))
    def get_items(self, obj):
        """Get token items"""
        items = obj.items.all()
        return TokenItemReadSerializer(items, many=True).data
    
    def get_barcode_image_url(self, obj):
        if obj.barcode_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.barcode_image.url) if request else obj.barcode_image.url
        return None

    def get_qrcode_image_url(self, obj):
        if obj.qrcode_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.qrcode_image.url) if request else obj.qrcode_image.url
        return None

class TokenStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating token status by token_code"""
    token_code = serializers.CharField(
        max_length=150,
        help_text='کد توکن'
    )
    
    def validate_token_code(self, value):
        """Validate that token exists"""
        if not Token.objects.filter(token_code=value).exists():
            raise serializers.ValidationError('توکن با این کد یافت نشد.')
        return value
    
    def validate(self, attrs):
        """Validate that token is not already received"""
        token_code = attrs.get('token_code')
        if token_code:
            try:
                token = Token.objects.get(token_code=token_code)
                if token.status == 'received':
                    raise serializers.ValidationError({
                        'token_code': f'توکن با کد "{token_code}" قبلاً دریافت شده است.'
                    })
            except Token.DoesNotExist:
                pass
        return attrs
    
    def update_status(self):
        """Update token status to received"""
        token_code = self.validated_data['token_code']
        token = Token.objects.get(token_code=token_code)
        token.status = 'received'
        token.save()
        return token
    
    @swagger_serializer_method(serializer_or_field=TokenItemReadSerializer(many=True))
    def get_items(self, obj):
        """Get token items"""
        items = obj.items.all()
        return TokenItemReadSerializer(items, many=True).data


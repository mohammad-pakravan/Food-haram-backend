from rest_framework import serializers
from datetime import date
import jdatetime
import secrets
import string
from django.db import transaction
from drf_yasg.utils import swagger_serializer_method
from drf_yasg import openapi

from .models import DirectSale, DirectSaleItem
from apps.foods.models import Food
from apps.ingredients.models import NORMAL_SUBCATEGORY_CHOICES, SUBCATEGORY_CHOICES
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
    """Serializer for food items in sale creation"""
    class Meta:
        ref_name = 'SaleFoodItem'
    
    food = serializers.PrimaryKeyRelatedField(queryset=Food.objects.all())
    count = serializers.IntegerField(min_value=1)


class DirectSaleItemReadSerializer(serializers.ModelSerializer):
    """Serializer for reading DirectSaleItem"""
    food_title = serializers.CharField(source='food.title', read_only=True)
    food_unit_price = serializers.DecimalField(source='food.unit_price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = DirectSaleItem
        fields = ['id', 'food', 'food_title', 'food_unit_price', 'count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DirectSaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating DirectSale with DirectSaleItems"""
    date = JalaliDateField()
    subcategory = serializers.ChoiceField(
        choices=NORMAL_SUBCATEGORY_CHOICES,
        write_only=True,
        help_text='زیر دسته‌بندی (همه فروش‌ها به صورت پیش‌فرض عادی هستند)'
    )
    foods = FoodItemSerializer(many=True)
    sale_code = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectSale
        fields = [
            'id',
            'sale_code',
            'date',
            'subcategory',
            'customer_name',
            'phone',
            'foods',
            'items',
            'total_price',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'sale_code', 'total_price', 'created_at', 'updated_at']
    
    def validate_foods(self, value):
        """Validate that at least one food item is provided"""
        if not value or len(value) == 0:
            raise serializers.ValidationError('حداقل یک غذا باید انتخاب شود.')
        return value
    
    def validate(self, attrs):
        """Validate that all foods match the subcategory and are normal category"""
        subcategory = attrs.get('subcategory')
        foods_data = attrs.get('foods')
        
        # All sales are normal by default, so category is always 'normal'
        category = 'normal'
        
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
                        # Check category (must be normal)
                        if food.category != category:
                            raise serializers.ValidationError({
                                'foods': f'غذای "{food.title}" از دسته‌بندی حضرتی است. همه فروش‌ها باید از دسته‌بندی عادی باشند.'
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
    
    @swagger_serializer_method(serializer_or_field=DirectSaleItemReadSerializer(many=True))
    def get_items(self, obj):
        """Get sale items"""
        items = obj.items.all()
        return DirectSaleItemReadSerializer(items, many=True).data
    
    def generate_sale_code(self):
        """Generate a random sale code"""
        # Generate 8-character alphanumeric code
        alphabet = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        # Check if code already exists, regenerate if needed
        while DirectSale.objects.filter(sale_code=code).exists():
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        return code
    
    @transaction.atomic
    def create(self, validated_data):
        """Create DirectSale and DirectSaleItems together, and decrease MenuPlan capacity"""
        foods_data = validated_data.pop('foods')
        subcategory = validated_data.pop('subcategory')  # We don't store subcategory in DirectSale model
        
        # Generate sale code
        sale_code = self.generate_sale_code()
        
        # Create DirectSale
        direct_sale = DirectSale.objects.create(
            sale_code=sale_code,
            **validated_data
        )
        
        # Calculate total price and create DirectSaleItems
        total_price = 0
        for food_item in foods_data:
            food = food_item['food']
            count = food_item['count']
            
            # Calculate price for this item
            item_price = food.unit_price * count
            total_price += item_price
            
            # Decrease MenuPlan capacity first (before creating DirectSaleItem)
            # Find MenuPlan with matching food, date, and meal_type
            menu_plan = MenuPlan.objects.filter(
                food=food,
                date=direct_sale.date,
                meal_type=food.meal_type
            ).first()
            
            if menu_plan:
                # Check if there's enough capacity
                if menu_plan.capacity < count:
                    raise serializers.ValidationError({
                        'foods': f'ظرفیت کافی برای غذای "{food.title}" وجود ندارد. ظرفیت موجود: {menu_plan.capacity}، درخواستی: {count}'
                    })
                
                # Decrease capacity
                menu_plan.capacity -= count
                menu_plan.save()
            else:
                # If no MenuPlan found, raise an error
                raise serializers.ValidationError({
                    'foods': f'برنامه غذایی برای غذای "{food.title}" در تاریخ {direct_sale.date} و نوع {food.get_meal_type_display()} یافت نشد.'
                })
            
            # Create DirectSaleItem after capacity check
            DirectSaleItem.objects.create(
                direct_sale=direct_sale,
                food=food,
                count=count
            )
        
        # Update total price
        direct_sale.total_price = total_price
        direct_sale.save()
        
        return direct_sale
    
    def to_representation(self, instance):
        """Remove foods from representation"""
        ret = super().to_representation(instance)
        ret.pop('foods', None)
        ret.pop('subcategory', None)  # Also remove subcategory from output
        return ret


class DirectSaleListSerializer(serializers.ModelSerializer):
    """Serializer for listing DirectSales"""
    date = JalaliDateField()
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectSale
        fields = [
            'id',
            'sale_code',
            'date',
            'customer_name',
            'phone',
            'total_price',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'sale_code', 'total_price', 'items', 'created_at', 'updated_at']
    
    @swagger_serializer_method(serializer_or_field=DirectSaleItemReadSerializer(many=True))
    def get_items(self, obj):
        """Get sale items"""
        items = obj.items.all()
        return DirectSaleItemReadSerializer(items, many=True).data


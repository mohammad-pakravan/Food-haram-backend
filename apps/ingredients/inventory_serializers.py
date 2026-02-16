from rest_framework import serializers
from datetime import date
import jdatetime
from decimal import Decimal
from django.db import transaction
from .models import InventoryStock, InventoryLog, Ingredient, MaterialConsumption, InventoryStockUpdate


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
    last_inspection_date = serializers.SerializerMethodField()
    last_inspected_by = serializers.SerializerMethodField()

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
            'last_inspection_date',
            'last_inspected_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ingredient_name', 'ingredient_category', 'ingredient_subcategory', 'ingredient_unit', 'warning_amount', 'is_low_stock', 'last_inspection_date', 'last_inspected_by']

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
    
    def get_last_inspection_date(self, obj):
        """Get last inspection date from InventoryStockUpdate"""
        from .models import InventoryStockUpdate
        last_update = InventoryStockUpdate.objects.filter(
            ingredient=obj.ingredient
        ).order_by('-inspection_date', '-created_at').first()
        if last_update:
            return JalaliDateField().to_representation(last_update.inspection_date)
        return None
    
    def get_last_inspected_by(self, obj):
        """Get username of last inspector"""
        from .models import InventoryStockUpdate
        last_update = InventoryStockUpdate.objects.filter(
            ingredient=obj.ingredient
        ).order_by('-inspection_date', '-created_at').first()
        if last_update and last_update.created_by:
            return last_update.created_by.username
        return None


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


class MaterialConsumptionSerializer(serializers.ModelSerializer):
    """Serializer for MaterialConsumption (مصرفی BOM)"""
    menu_plan_id = serializers.IntegerField(source='menu_plan.id', read_only=True)
    menu_plan_food_title = serializers.CharField(source='menu_plan.food.title', read_only=True)
    menu_plan_date = serializers.CharField(source='menu_plan.date', read_only=True)
    menu_plan_meal_type = serializers.CharField(source='menu_plan.meal_type', read_only=True)
    menu_plan_capacity = serializers.IntegerField(source='menu_plan.capacity', read_only=True)
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_code = serializers.CharField(source='ingredient.code', read_only=True)
    ingredient_unit = serializers.CharField(source='ingredient.unit', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = MaterialConsumption
        fields = [
            'id',
            'menu_plan',
            'menu_plan_id',
            'menu_plan_food_title',
            'menu_plan_date',
            'menu_plan_meal_type',
            'menu_plan_capacity',
            'ingredient',
            'ingredient_name',
            'ingredient_code',
            'ingredient_unit',
            'consumed_amount',
            'unit',
            'notes',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'menu_plan_id', 'menu_plan_food_title', 'menu_plan_date',
            'menu_plan_meal_type', 'menu_plan_capacity',
            'ingredient_name', 'ingredient_code', 'ingredient_unit',
            'created_by_username'
        ]

    def validate_menu_plan(self, value):
        """اعتبارسنجی که menu_plan.cook_status = 'done' باشد"""
        if value.cook_status != 'done':
            raise serializers.ValidationError('فقط برای برنامه‌های غذایی با وضعیت "پخته شده" می‌توان مصرفی ثبت کرد.')
        return value

    def validate(self, attrs):
        """اعتبارسنجی‌های اضافی"""
        menu_plan = attrs.get('menu_plan')
        ingredient = attrs.get('ingredient')
        
        if menu_plan and ingredient:
            # اعتبارسنجی category/subcategory match
            food = menu_plan.food
            if food.category != ingredient.category:
                from .models import CATEGORY_TYPE_CHOICES
                category_dict = dict(CATEGORY_TYPE_CHOICES)
                raise serializers.ValidationError({
                    'ingredient': f'دسته‌بندی ماده اولیه با دسته‌بندی غذا مطابقت ندارد.'
                })
            
            if food.subcategory != ingredient.subcategory:
                raise serializers.ValidationError({
                    'ingredient': f'زیر دسته‌بندی ماده اولیه با زیر دسته‌بندی غذا مطابقت ندارد.'
                })
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """ایجاد MaterialConsumption و کسر از موجودی"""
        # تنظیم created_by از request.user
        validated_data['created_by'] = self.context['request'].user
        
        # ایجاد MaterialConsumption
        material_consumption = MaterialConsumption.objects.create(**validated_data)
        
        # کسر از موجودی InventoryStock
        ingredient = material_consumption.ingredient
        inventory_stock, created = InventoryStock.objects.get_or_create(
            ingredient=ingredient,
            defaults={'total_amount': 0}
        )
        
        # تبدیل واحد و کسر از موجودی (فرض می‌کنیم واحدها یکسان هستند)
        consumed_amount = float(material_consumption.consumed_amount)
        if inventory_stock.total_amount >= consumed_amount:
            inventory_stock.total_amount -= consumed_amount
            inventory_stock.save()
        else:
            # اگر موجودی کافی نباشد، خطا نمی‌دهیم اما می‌توانیم warning بدهیم
            # یا می‌توانیم موجودی را صفر کنیم
            inventory_stock.total_amount = 0
            inventory_stock.save()
        
        return material_consumption


class InventoryStockUpdateSerializer(serializers.ModelSerializer):
    """Serializer for InventoryStockUpdate (ثبت موجودی واقعی)"""
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_code = serializers.CharField(source='ingredient.code', read_only=True)
    ingredient_unit = serializers.CharField(source='ingredient.unit', read_only=True)
    inspection_date = JalaliDateField(required=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = InventoryStockUpdate
        fields = [
            'id',
            'ingredient',
            'ingredient_name',
            'ingredient_code',
            'ingredient_unit',
            'actual_amount',
            'inspection_date',
            'notes',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by',
            'ingredient_name', 'ingredient_code', 'ingredient_unit',
            'created_by_username'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """ایجاد InventoryStockUpdate و به‌روزرسانی InventoryStock"""
        # تنظیم created_by از request.user
        validated_data['created_by'] = self.context['request'].user
        
        # ایجاد InventoryStockUpdate
        stock_update = InventoryStockUpdate.objects.create(**validated_data)
        
        # به‌روزرسانی InventoryStock
        ingredient = stock_update.ingredient
        inventory_stock, created = InventoryStock.objects.get_or_create(
            ingredient=ingredient,
            defaults={'total_amount': 0}
        )
        
        # به‌روزرسانی موجودی و تاریخ
        inventory_stock.total_amount = float(stock_update.actual_amount)
        inventory_stock.last_received_date = stock_update.inspection_date
        inventory_stock.save()
        
        return stock_update



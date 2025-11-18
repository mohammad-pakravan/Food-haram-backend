from rest_framework import serializers
from datetime import date
import jdatetime

from .models import MenuPlan


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


class MenuPlanSerializer(serializers.ModelSerializer):
    food_title = serializers.CharField(source='food.title', read_only=True)
    food_category = serializers.CharField(source='food.category', read_only=True)
    dessert_title = serializers.CharField(source='dessert.title', read_only=True, allow_null=True)
    date_jalali = JalaliDateField(source='date', read_only=False, required=False)
    date = serializers.DateField(required=False, write_only=True)

    class Meta:
        model = MenuPlan
        fields = [
            'id',
            'date',
            'date_jalali',
            'food',
            'food_title',
            'food_category',
            'meal_type',
            'capacity',
            'dessert',
            'dessert_title',
            'dessert_count',
            'cook_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'food_title', 'food_category', 'dessert_title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if user is restaurant manager (not central)
        request = self.context.get('request')
        if request and request.user:
            # Restaurant managers can't edit cook_status, only view it
            if not request.user.is_central and request.user.has_role('restaurant_manager'):
                self.fields['cook_status'].read_only = True

    def validate(self, attrs):
        """Ensure date is provided either as date or date_jalali"""
        # date_jalali will be converted to date in to_internal_value
        # So if date_jalali is in initial_data, it will be in attrs as 'date' after conversion
        date_value = attrs.get('date')
        
        # Check initial_data for date_jalali if date is not provided
        if not date_value and not self.instance:
            initial_data = getattr(self, 'initial_data', {})
            if 'date_jalali' not in initial_data and 'date' not in initial_data:
                raise serializers.ValidationError({'date_jalali': 'تاریخ الزامی است.'})
        
        # Ensure cook_status defaults to 'pending' if not provided
        if 'cook_status' not in attrs and not self.instance:
            attrs['cook_status'] = 'pending'
        
        return attrs


from rest_framework import serializers

from apps.ingredients.models import Ingredient, CATEGORY_TYPE_CHOICES, SUBCATEGORY_CHOICES
from .models import Dessert, Food, FoodIngredient


class FoodIngredientWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount_per_serving = serializers.IntegerField(min_value=0)


class FoodIngredientReadSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_category = serializers.SerializerMethodField()
    ingredient_subcategory = serializers.SerializerMethodField()

    class Meta:
        model = FoodIngredient
        fields = ['id', 'ingredient', 'ingredient_name', 'ingredient_category', 'ingredient_subcategory', 'amount_per_serving']
        read_only_fields = ['id', 'ingredient_name', 'ingredient_category', 'ingredient_subcategory']

    def get_ingredient_category(self, obj):
        """Return Persian label for ingredient category"""
        from apps.ingredients.models import CATEGORY_TYPE_CHOICES
        category_dict = dict(CATEGORY_TYPE_CHOICES)
        return category_dict.get(obj.ingredient.category, obj.ingredient.category)

    def get_ingredient_subcategory(self, obj):
        """Return Persian label for ingredient subcategory"""
        from apps.ingredients.models import SUBCATEGORY_CHOICES
        subcategory_dict = dict(SUBCATEGORY_CHOICES)
        return subcategory_dict.get(obj.ingredient.subcategory, obj.ingredient.subcategory)


class FoodManagementSerializer(serializers.ModelSerializer):
    ingredients = FoodIngredientWriteSerializer(many=True, required=False, write_only=True)
    ingredients_detail = FoodIngredientReadSerializer(source='ingredients', many=True, read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    category_value = serializers.CharField(source='category', write_only=True, required=False)
    subcategory_value = serializers.CharField(source='subcategory', write_only=True, required=False)

    class Meta:
        model = Food
        fields = [
            'id',
            'title',
            'category',
            'subcategory',
            'category_value',
            'subcategory_value',
            'meal_type',
            'preparation_time',
            'unit_price',
            'ingredients',
            'ingredients_detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'ingredients_detail', 'created_at', 'updated_at', 'category', 'subcategory']

    def get_category(self, obj):
        """Return Persian label for category"""
        category_dict = dict(CATEGORY_TYPE_CHOICES)
        return category_dict.get(obj.category, obj.category)

    def get_subcategory(self, obj):
        """Return Persian label for subcategory"""
        subcategory_dict = dict(SUBCATEGORY_CHOICES)
        return subcategory_dict.get(obj.subcategory, obj.subcategory)

    def validate(self, attrs):
        # Handle category_value and subcategory_value for input
        if 'category_value' in attrs:
            attrs['category'] = attrs.pop('category_value')
        if 'subcategory_value' in attrs:
            attrs['subcategory'] = attrs.pop('subcategory_value')
        
        ingredients = attrs.get('ingredients')
        category = attrs.get('category')
        subcategory = attrs.get('subcategory')

        if self.instance:
            if category is None:
                category = self.instance.category
            if subcategory is None:
                subcategory = self.instance.subcategory

        if not self.instance and not ingredients:
            raise serializers.ValidationError({'ingredients': 'حداقل یک ماده اولیه برای ایجاد غذا الزامی است.'})

        # Validate subcategory matches category
        if category and subcategory:
            from apps.ingredients.models import CATEGORY_SUBCATEGORY_MAP
            valid_subcategories = CATEGORY_SUBCATEGORY_MAP.get(category, [])
            if subcategory not in valid_subcategories:
                category_dict = dict(CATEGORY_TYPE_CHOICES)
                category_label = category_dict.get(category, category)
                raise serializers.ValidationError({
                    'subcategory_value': f'زیر دسته‌بندی انتخاب شده با دسته‌بندی {category_label} مطابقت ندارد.'
                })

        if ingredients:
            for item in ingredients:
                ingredient = item['ingredient']
                # Check category match
                if ingredient.category != category:
                    category_dict = dict(CATEGORY_TYPE_CHOICES)
                    ingredient_category_label = category_dict.get(ingredient.category, ingredient.category)
                    raise serializers.ValidationError({
                        'ingredients': f"ماده اولیه «{ingredient.name}» نوع {ingredient_category_label} هست که با نوع غذا مطابقت نداره"
                    })
                # Check subcategory match
                if ingredient.subcategory != subcategory:
                    subcategory_dict = dict(SUBCATEGORY_CHOICES)
                    ingredient_subcategory_label = subcategory_dict.get(ingredient.subcategory, ingredient.subcategory)
                    raise serializers.ValidationError({
                        'ingredients': f"ماده اولیه «{ingredient.name}» زیر دسته‌بندی {ingredient_subcategory_label} هست که با زیر دسته‌بندی غذا مطابقت نداره"
                    })
        elif category and subcategory and self.instance:
            # Check if existing ingredients match new category/subcategory
            category_mismatch = self.instance.ingredients.exclude(
                ingredient__category=category
            ).exists()
            subcategory_mismatch = self.instance.ingredients.exclude(
                ingredient__subcategory=subcategory
            ).exists()
            if category_mismatch or subcategory_mismatch:
                raise serializers.ValidationError({
                    'category': 'برای تغییر دسته‌بندی یا زیر دسته‌بندی باید مواد اولیه را نیز به‌روزرسانی کنید.'
                })

        return attrs

    def _sync_ingredients(self, food: Food, ingredients_data):
        if ingredients_data is None:
            return
        food.ingredients.all().delete()
        FoodIngredient.objects.bulk_create([
            FoodIngredient(
                food=food,
                ingredient=item['ingredient'],
                amount_per_serving=item['amount_per_serving'],
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        food = Food.objects.create(**validated_data)
        self._sync_ingredients(food, ingredients_data)
        return food

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._sync_ingredients(instance, ingredients_data)
        return instance

class DessertSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    category_value = serializers.CharField(source='category', write_only=True, required=False)
    subcategory_value = serializers.CharField(source='subcategory', write_only=True, required=False)

    class Meta:
        model = Dessert
        fields = [
            'id',
            'title',
            'category',
            'subcategory',
            'category_value',
            'subcategory_value',
            'unit_price',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'category', 'subcategory']

    def get_category(self, obj):
        """Return Persian label for category"""
        category_dict = dict(CATEGORY_TYPE_CHOICES)
        return category_dict.get(obj.category, obj.category)

    def get_subcategory(self, obj):
        """Return Persian label for subcategory"""
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
            from apps.ingredients.models import CATEGORY_SUBCATEGORY_MAP
            valid_subcategories = CATEGORY_SUBCATEGORY_MAP.get(category, [])
            if subcategory not in valid_subcategories:
                category_dict = dict(CATEGORY_TYPE_CHOICES)
                category_label = category_dict.get(category, category)
                raise serializers.ValidationError({
                    'subcategory_value': f'زیر دسته‌بندی انتخاب شده با دسته‌بندی {category_label} مطابقت ندارد.'
                })
        
        return attrs


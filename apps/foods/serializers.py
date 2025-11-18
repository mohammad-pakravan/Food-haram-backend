from rest_framework import serializers

from apps.ingredients.models import Ingredient, CATEGORY_TYPE_CHOICES
from .models import Food, FoodIngredient


class FoodIngredientWriteSerializer(serializers.Serializer):
    ingredient = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount_per_serving = serializers.IntegerField(min_value=0)


class FoodIngredientReadSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_category = serializers.CharField(source='ingredient.category', read_only=True)

    class Meta:
        model = FoodIngredient
        fields = ['id', 'ingredient', 'ingredient_name', 'ingredient_category', 'amount_per_serving']
        read_only_fields = ['id', 'ingredient_name', 'ingredient_category']


class FoodManagementSerializer(serializers.ModelSerializer):
    ingredients = FoodIngredientWriteSerializer(many=True, required=False, write_only=True)
    ingredients_detail = FoodIngredientReadSerializer(source='ingredients', many=True, read_only=True)

    class Meta:
        model = Food
        fields = [
            'id',
            'title',
            'category',
            'meal_type',
            'preparation_time',
            'unit_price',
            'ingredients',
            'ingredients_detail',
        ]
        read_only_fields = ['id', 'ingredients_detail']

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        category = attrs.get('category')

        if self.instance and category is None:
            category = self.instance.category

        if not self.instance and not ingredients:
            raise serializers.ValidationError({'ingredients': 'حداقل یک ماده اولیه برای ایجاد غذا الزامی است.'})

        if ingredients:
            for item in ingredients:
                ingredient = item['ingredient']
                if ingredient.category != category:
                    category_dict = dict(CATEGORY_TYPE_CHOICES)
                    ingredient_category_label = category_dict.get(ingredient.category, ingredient.category)
                    raise serializers.ValidationError({
                        'ingredients': f"ماده اولیه «{ingredient.name}» نوع {ingredient_category_label} هست که با نوع غذا مطابقت نداره"
                    })
        elif category and self.instance:
            mismatch_exists = self.instance.ingredients.exclude(
                ingredient__category=category
            ).exists()
            if mismatch_exists:
                raise serializers.ValidationError({
                    'category': 'برای تغییر دسته‌بندی باید مواد اولیه را نیز به‌روزرسانی کنید.'
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


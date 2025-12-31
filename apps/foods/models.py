from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django_jalali.db import models as jmodels

from apps.ingredients.models import (
    Ingredient, 
    CATEGORY_TYPE_CHOICES, 
    SUBCATEGORY_CHOICES,
    CATEGORY_SUBCATEGORY_MAP
)


MEAL_TYPE_CHOICES = [
    ('breakfast', 'صبحانه'),
    ('lunch', 'ناهار'),
    ('dinner', 'شام'),
]


class Food(models.Model):
    objects = jmodels.jManager()
    title = models.CharField(
        max_length=150,
        verbose_name='نام غذا',
        validators=[MinLengthValidator(2)],
    )
    category = models.CharField(
        max_length=150,
        choices=CATEGORY_TYPE_CHOICES,
        verbose_name='دسته بندی',
        validators=[MinLengthValidator(2)],
    )
    subcategory = models.CharField(
        max_length=150,
        choices=SUBCATEGORY_CHOICES,
        verbose_name='زیر دسته بندی',
        validators=[MinLengthValidator(2)],
    )
    meal_types = ArrayField(
        models.CharField(max_length=50, choices=MEAL_TYPE_CHOICES),
        size=None,
        default=list,
        verbose_name='نوع غذا',
        help_text='وعده‌های غذایی (می‌توانید چند مورد را انتخاب کنید)',
    )
    preparation_time = models.IntegerField(
        verbose_name='زمان آماده سازی',
        validators=[MinValueValidator(0)],
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت واحد',
        validators=[MinValueValidator(0)],
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'غذا'
        verbose_name_plural = 'غذاها'
        ordering = ['title']

    def clean(self):
        # Validate that subcategory matches category
        if self.category and self.subcategory:
            valid_subcategories = CATEGORY_SUBCATEGORY_MAP.get(self.category, [])
            if self.subcategory not in valid_subcategories:
                category_label = dict(CATEGORY_TYPE_CHOICES).get(self.category, self.category)
                raise ValidationError({
                    'subcategory': f'زیر دسته‌بندی انتخاب شده با دسته‌بندی {category_label} مطابقت ندارد.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class FoodIngredient(models.Model):
    objects = jmodels.jManager()
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='غذا',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='food_usages',
        verbose_name='ماده اولیه',
    )
    amount_per_serving = models.IntegerField(
        verbose_name='مقدار برای هر سرو',
        validators=[MinValueValidator(0)],
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'مواد اولیه غذا'
        verbose_name_plural = 'مواد اولیه غذاها'
        ordering = ['food']

    def __str__(self) -> str:
        return f"{self.food.title} - {self.ingredient.name}"

    def clean(self):
        if self.food_id and self.ingredient_id:
            food = self.food
            ingredient = self.ingredient
            
            # Check category match
            if food.category != ingredient.category:
                category_dict = dict(CATEGORY_TYPE_CHOICES)
                ingredient_category_label = category_dict.get(ingredient.category, ingredient.category)
                raise ValidationError({
                    'ingredient': f'نوع ماده {ingredient_category_label} هست که با نوع غذا مطابقت نداره'
                })
            
            # Check subcategory match
            if food.subcategory != ingredient.subcategory:
                subcategory_dict = dict(SUBCATEGORY_CHOICES)
                ingredient_subcategory_label = subcategory_dict.get(ingredient.subcategory, ingredient.subcategory)
                raise ValidationError({
                    'ingredient': f'زیر دسته‌بندی ماده اولیه {ingredient_subcategory_label} هست که با زیر دسته‌بندی غذا مطابقت نداره'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Dessert(models.Model):
    objects = jmodels.jManager()
    title = models.CharField(
        max_length=150,
        verbose_name='نام دسر',
        validators=[MinLengthValidator(2)],
    )
    category = models.CharField(
        max_length=150,
        choices=CATEGORY_TYPE_CHOICES,
        verbose_name='دسته بندی',
        validators=[MinLengthValidator(2)],
    )
    subcategory = models.CharField(
        max_length=150,
        choices=SUBCATEGORY_CHOICES,
        verbose_name='زیر دسته بندی',
        validators=[MinLengthValidator(2)],
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت واحد',
        validators=[MinValueValidator(0)],
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'دسر'
        verbose_name_plural = 'دسرها'
        ordering = ['title']

    def clean(self):
        # Validate that subcategory matches category
        if self.category and self.subcategory:
            valid_subcategories = CATEGORY_SUBCATEGORY_MAP.get(self.category, [])
            if self.subcategory not in valid_subcategories:
                category_label = dict(CATEGORY_TYPE_CHOICES).get(self.category, self.category)
                raise ValidationError({
                    'subcategory': f'زیر دسته‌بندی انتخاب شده با دسته‌بندی {category_label} مطابقت ندارد.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title

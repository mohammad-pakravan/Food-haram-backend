from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django.core.exceptions import ValidationError

from apps.ingredients.models import Ingredient, CATEGORY_TYPE_CHOICES


MEAL_TYPE_CHOICES = [
    ('breakfast', 'صبحانه'),
    ('lunch', 'ناهار'),
    ('dinner', 'شام'),
]


class Food(models.Model):
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
    meal_type = models.CharField(
        max_length=150,
        choices=MEAL_TYPE_CHOICES,
        verbose_name='نوع غذا',
        validators=[MinLengthValidator(2)],
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

    class Meta:
        verbose_name = 'غذا'
        verbose_name_plural = 'غذاها'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class FoodIngredient(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'مواد اولیه غذا'
        verbose_name_plural = 'مواد اولیه غذاها'
        ordering = ['food']

    def __str__(self) -> str:
        return f"{self.food.title} - {self.ingredient.name}"

    def clean(self):
        if self.food_id and self.ingredient_id:
            if self.food.category != self.ingredient.category:
                category_dict = dict(CATEGORY_TYPE_CHOICES)
                ingredient_category_label = category_dict.get(self.ingredient.category, self.ingredient.category)
                raise ValidationError({
                    'ingredient': f'نوع ماده {ingredient_category_label} هست که با نوع غذا مطابقت نداره'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Dessert(models.Model):
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
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت واحد',
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'دسر'
        verbose_name_plural = 'دسرها'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title

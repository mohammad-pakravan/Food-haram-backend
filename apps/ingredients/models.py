from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator


UNIT_CHOICES = [
    ('kg', 'کیلوگرم'),
    ('g', 'گرم'),
    ('mg', 'میلی‌گرم'),
    ('ton', 'تن'),
    ('l', 'لیتر'),
    ('ml', 'میلی‌لیتر'),
    ('cup', 'پیمانه / لیوان'),
    ('tbsp', 'قاشق غذاخوری'),
    ('tsp', 'قاشق چای‌خوری'),
    ('pcs', 'عدد'),
    ('pack', 'بسته'),
    ('carton', 'کارتن'),
    ('dozen', 'شل / دوجین'),
    ('set', 'دست / مجموعه'),
    ('tray', 'سینی'),
    ('bag', 'کیسه / گونی'),
]

CATEGORY_TYPE_CHOICES = [
    ('noraml', 'عادی'),
    ('hazrati', 'حضرتی'),
]


class Ingredient(models.Model):
    category = models.CharField(
        max_length=150,
        choices=CATEGORY_TYPE_CHOICES,
        verbose_name='دسته بندی',
        validators=[MinLengthValidator(2)],
    )
    name = models.CharField(
        max_length=150,
        verbose_name='نام ماده اولیه',
        validators=[MinLengthValidator(2)],
    )
    unit = models.CharField(
        max_length=150,
        choices=UNIT_CHOICES,
        verbose_name='واحد',
        validators=[MinLengthValidator(1)],
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت واحد',
        validators=[MinValueValidator(0)],
    )
    code = models.CharField(
        max_length=150,
        verbose_name='کد',
        validators=[MinLengthValidator(2)],
    )
    warning_amount = models.IntegerField(
        verbose_name='مقدار هشدار موجودی',
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'ماده اولیه'
        verbose_name_plural = 'مواد اولیه'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class InventoryStock(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='stock_entries',
        verbose_name='ماده اولیه',
    )
    total_amount = models.FloatField(
        verbose_name='مقدار موجودی',
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'موجودی ماده اولیه'
        verbose_name_plural = 'موجودی مواد اولیه'
        ordering = ['ingredient']

    def __str__(self) -> str:
        return f"{self.ingredient.name} - {self.total_amount}"


class InventoryLog(models.Model):
    inventory = models.ForeignKey(
        InventoryStock,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='موجودی ماده اولیه',
    )
    amount = models.IntegerField(
        verbose_name='تغییر موجودی',
        validators=[MinValueValidator(0)],
    )
    unit = models.CharField(
        max_length=150,
        choices=UNIT_CHOICES,
        verbose_name='واحد',
        validators=[MinLengthValidator(1)],
    )
    code = models.CharField(
        max_length=150,
        verbose_name='کد',
        validators=[MinLengthValidator(2)],
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'لاگ موجودی ماده اولیه'
        verbose_name_plural = 'لاگ‌های موجودی مواد اولیه'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.inventory.ingredient.name} - {self.amount}"

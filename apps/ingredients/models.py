from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django_jalali.db import models as jmodels


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

# Subcategory choices for hazrati (حضرتی)
HAZRATI_SUBCATEGORY_CHOICES = [
    ('needy', 'نیازمندان'),
    ('ceremonies', 'مراسمات'),
    ('honorary', 'تکریمی'),
    ('lottery', 'قرعه کشی'),
]

# Subcategory choices for normal (عادی)
NORMAL_SUBCATEGORY_CHOICES = [
    ('participatory_camps', 'اردوهای مشارکتی'),
    ('staff', 'پرسنل'),
    ('sales', 'فروشی'),
]

# All subcategory choices combined
SUBCATEGORY_CHOICES = HAZRATI_SUBCATEGORY_CHOICES + NORMAL_SUBCATEGORY_CHOICES

# Mapping category to valid subcategories
CATEGORY_SUBCATEGORY_MAP = {
    'hazrati': [choice[0] for choice in HAZRATI_SUBCATEGORY_CHOICES],
    'noraml': [choice[0] for choice in NORMAL_SUBCATEGORY_CHOICES],
}


class Ingredient(models.Model):
    objects = jmodels.jManager()
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
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'ماده اولیه'
        verbose_name_plural = 'مواد اولیه'
        ordering = ['name']

    def clean(self):
        from django.core.exceptions import ValidationError
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
        return self.name


class InventoryStock(models.Model):
    objects = jmodels.jManager()
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
    last_received_date = jmodels.jDateField(
        verbose_name='تاریخ آخرین تحویل',
        null=True,
        blank=True,
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'موجودی ماده اولیه'
        verbose_name_plural = 'موجودی مواد اولیه'
        ordering = ['ingredient']

    def __str__(self) -> str:
        return f"{self.ingredient.name} - {self.total_amount}"


class InventoryLog(models.Model):
    objects = jmodels.jManager()
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
    date = jmodels.jDateField(
        verbose_name='تاریخ تحویل',
        null=True,
        blank=True,
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'لاگ موجودی ماده اولیه'
        verbose_name_plural = 'لاگ‌های موجودی مواد اولیه'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.inventory.ingredient.name} - {self.amount}"

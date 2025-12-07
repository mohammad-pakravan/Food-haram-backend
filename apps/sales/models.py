from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django_jalali.db import models as jmodels

from apps.foods.models import Food


class DirectSale(models.Model):
    objects = jmodels.jManager()
    customer_name = models.CharField(
        max_length=150,
        verbose_name='نام مشتری',
        validators=[MinLengthValidator(2)],
    )
    phone = models.CharField(
        max_length=150,
        verbose_name='تلفن مشتری',
        validators=[MinLengthValidator(2)],
        blank=True,
        null=True,
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت کل',
        validators=[MinValueValidator(0)],
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'فروش مستقیم'
        verbose_name_plural = 'فروش‌های مستقیم'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.customer_name} - {self.total_price}"


class DirectSaleItem(models.Model):
    objects = jmodels.jManager()
    direct_sale = models.ForeignKey(
        DirectSale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='فروش مستقیم',
    )
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='direct_sale_items',
        verbose_name='غذا',
    )
    count = models.IntegerField(
        verbose_name='تعداد',
        validators=[MinValueValidator(0)],
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'آیتم فروش مستقیم'
        verbose_name_plural = 'آیتم‌های فروش مستقیم'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.direct_sale.customer_name} - {self.food.title}"

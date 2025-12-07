from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django_jalali.db import models as jmodels

from apps.foods.models import Food, Dessert, MEAL_TYPE_CHOICES


COOK_STATUS_CHOICES = [
    ('pending', 'در انتظار'),
    ('cooking', 'در حال پخت'),
    ('done', 'پخته شده'),
]


class MenuPlan(models.Model):
    objects = jmodels.jManager()
    date = jmodels.jDateField(verbose_name='تاریخ')
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='menu_plans',
        verbose_name='غذا',
    )
    meal_type = models.CharField(
        max_length=150,
        choices=MEAL_TYPE_CHOICES,
        verbose_name='نوع غذا',
        validators=[MinLengthValidator(2)],
    )
    capacity = models.IntegerField(
        verbose_name='ظرفیت',
        validators=[MinValueValidator(0)],
    )
    dessert = models.ForeignKey(
        Dessert,
        on_delete=models.CASCADE,
        related_name='menu_plans',
        verbose_name='دسر',
        null=True,
        blank=True,
    )
    dessert_count = models.IntegerField(
        verbose_name='تعداد دسر',
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )
    cook_status = models.CharField(
        max_length=50,
        choices=COOK_STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت پخت',
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'برنامه غذایی'
        verbose_name_plural = 'برنامه‌های غذایی'
        ordering = ['-date', 'meal_type']

    def __str__(self) -> str:
        return f"{self.food.title} ({self.date})"

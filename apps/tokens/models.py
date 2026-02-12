from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator
from django_jalali.db import models as jmodels

import os
from io import BytesIO
from django.core.files import File
import barcode
from barcode.writer import ImageWriter
import qrcode

from apps.foods.models import Food


STATUS_CHOICES = [
    ('pending', 'در انتظار دریافت'),
    ('received', 'دریافت شده'),
]


class Token(models.Model):
    objects = jmodels.jManager()
    token_code = models.CharField(
        max_length=150,
        verbose_name='توکن',
        validators=[MinLengthValidator(2)],
    )
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
    date = jmodels.jDateField(verbose_name='تاریخ')
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت کل',
        validators=[MinValueValidator(0)],
        default=0,
    )
    barcode_image = models.ImageField(
        upload_to='barcodes/',   
        blank=True,
        null=True,
        verbose_name='بارکد'
    )
    qrcode_image = models.ImageField(
        upload_to='qrcodes/',   
        blank=True,
        null=True,
        verbose_name='QrCode'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت',
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    def save(self, *args, **kwargs):
        # اول ذخیره اصلی برای داشتن ID و token_code
        super().save(*args, **kwargs)

        updated = False

        if self.token_code:
            # --- Generate Barcode ---
            if not self.barcode_image:
                CODE128 = barcode.get_barcode_class('code128')
                code = CODE128(self.token_code, writer=ImageWriter())
                buffer = BytesIO()
                code.write(buffer)
                buffer.seek(0)  # مهم
                filename = f"{self.token_code}_barcode.png"
                self.barcode_image.save(filename, File(buffer), save=False)
                updated = True

            # --- Generate QR Code ---
            if not self.qrcode_image:
                qr_img = qrcode.make(self.token_code)
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                filename = f"{self.token_code}_qrcode.png"
                self.qrcode_image.save(filename, File(qr_buffer), save=False)
                updated = True

        if updated:
            # فقط یکبار save دوباره
            super().save(update_fields=['barcode_image', 'qrcode_image'])

    class Meta:
        verbose_name = 'توکن'
        verbose_name_plural = 'توکن‌ها'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.token_code} - {self.customer_name}"
    class Meta:
        verbose_name = 'توکن'
        verbose_name_plural = 'توکن‌ها'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.token_code} - {self.customer_name}"
    

class TokenItem(models.Model):
    objects = jmodels.jManager()
    token = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='توکن',
    )
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='token_items',
        verbose_name='غذا',
    )
    meal_type = models.CharField(
        max_length=50,
        choices=[('breakfast', 'صبحانه'), ('lunch', 'ناهار'), ('dinner', 'شام')],
        verbose_name='وعده غذایی',
        help_text='وعده غذایی که این آیتم برای آن صادر شده است',
        default='lunch',  # Default to lunch for backward compatibility
    )
    count = models.IntegerField(
        verbose_name='تعداد',
        validators=[MinValueValidator(0)],
    )
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')

    class Meta:
        verbose_name = 'آیتم توکن'
        verbose_name_plural = 'اقلام توکن'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.token.token_code} - {self.food.title}"

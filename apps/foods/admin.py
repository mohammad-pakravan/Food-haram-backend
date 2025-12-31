from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django import forms

from .models import Food, Dessert, FoodIngredient, MEAL_TYPE_CHOICES


class FoodIngredientInline(admin.TabularInline):
    model = FoodIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'amount_per_serving')


class FoodAdminForm(forms.ModelForm):
    """Custom form for Food admin with multiple select for meal_types"""
    meal_types = forms.MultipleChoiceField(
        choices=MEAL_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text='حداقل یک وعده غذایی را انتخاب کنید'
    )
    
    class Meta:
        model = Food
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Set initial value from instance
            self.fields['meal_types'].initial = self.instance.meal_types
    
    def clean_meal_types(self):
        meal_types = self.cleaned_data.get('meal_types')
        if not meal_types or len(meal_types) == 0:
            raise forms.ValidationError('حداقل یک وعده غذایی باید انتخاب شود.')
        return meal_types


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    form = FoodAdminForm
    list_display = ('title', 'category', 'meal_types_display', 'preparation_time', 'unit_price', 'created_at', 'updated_at')
    list_filter = ('category',)
    search_fields = ('title',)
    ordering = ('title',)
    inlines = (FoodIngredientInline,)
    readonly_fields = ('created_at', 'updated_at')
    
    def meal_types_display(self, obj):
        """Display meal types as comma-separated Persian labels"""
        meal_type_dict = dict(MEAL_TYPE_CHOICES)
        if obj.meal_types:
            return ', '.join([meal_type_dict.get(mt, mt) for mt in obj.meal_types])
        return '-'
    meal_types_display.short_description = 'وعده‌های غذایی'


@admin.register(Dessert)
class DessertAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'unit_price', 'created_at', 'updated_at')
    list_filter = ('category',)
    search_fields = ('title',)
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')

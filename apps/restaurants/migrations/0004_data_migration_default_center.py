# Generated manually for data migration

from django.db import migrations


def create_default_center_and_assign_restaurants(apps, schema_editor):
    """Create default center and assign existing restaurants to it"""
    Center = apps.get_model('restaurants', 'Center')
    Restaurant = apps.get_model('restaurants', 'Restaurant')
    
    # Create default center if it doesn't exist
    default_center, created = Center.objects.get_or_create(
        name='مرکز پیش‌فرض',
        defaults={
            'description': 'مرکز پیش‌فرض برای رستوران‌های موجود',
            'is_active': True
        }
    )
    
    # Assign all restaurants without center to default center
    Restaurant.objects.filter(center__isnull=True).update(center=default_center)


def reverse_migration(apps, schema_editor):
    """Reverse migration (optional)"""
    # Implement this section if needed
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0002_center_alter_restaurant_options_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_center_and_assign_restaurants, reverse_migration),
    ]


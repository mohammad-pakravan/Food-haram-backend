# Generated manually to convert JSONField to ArrayField

from django.db import migrations
import django.contrib.postgres.fields
from django.db import models


def convert_json_to_array(apps, schema_editor):
    """Convert JSONField data to ArrayField format using raw SQL"""
    with schema_editor.connection.cursor() as cursor:
        # Convert JSONB array to PostgreSQL array and copy to temp field
        cursor.execute("""
            UPDATE foods_food 
            SET meal_types_temp = ARRAY(SELECT jsonb_array_elements_text(meal_types::jsonb))
            WHERE meal_types IS NOT NULL 
            AND jsonb_typeof(meal_types::jsonb) = 'array'
        """)
        # Handle empty arrays or null values
        cursor.execute("""
            UPDATE foods_food 
            SET meal_types_temp = ARRAY[]::text[]
            WHERE meal_types_temp IS NULL
        """)


def reverse_convert_array_to_json(apps, schema_editor):
    """Reverse conversion - convert array back to JSON"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            UPDATE foods_food 
            SET meal_types = to_jsonb(meal_types)
            WHERE meal_types IS NOT NULL
        """)


class Migration(migrations.Migration):

    dependencies = [
        ("foods", "0008_remove_food_meal_type_food_meal_types"),
    ]

    operations = [
        # Step 1: Add a temporary ArrayField column
        migrations.AddField(
            model_name="food",
            name="meal_types_temp",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[('breakfast', 'صبحانه'), ('lunch', 'ناهار'), ('dinner', 'شام')],
                    max_length=50
                ),
                default=list,
                null=True,
                blank=True,
                size=None,
            ),
        ),
        # Step 2: Copy data from JSONField to ArrayField
        migrations.RunPython(
            code=convert_json_to_array,
            reverse_code=reverse_convert_array_to_json,
        ),
        # Step 3: Remove old JSONField column
        migrations.RemoveField(
            model_name="food",
            name="meal_types",
        ),
        # Step 4: Rename temp field to meal_types
        migrations.RenameField(
            model_name="food",
            old_name="meal_types_temp",
            new_name="meal_types",
        ),
        # Step 5: Set proper attributes on the final field
        migrations.AlterField(
            model_name="food",
            name="meal_types",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[('breakfast', 'صبحانه'), ('lunch', 'ناهار'), ('dinner', 'شام')],
                    max_length=50
                ),
                default=list,
                help_text='وعده\u200cهای غذایی (می\u200cتوانید چند مورد را انتخاب کنید)',
                size=None,
                verbose_name="نوع غذا",
            ),
        ),
    ]

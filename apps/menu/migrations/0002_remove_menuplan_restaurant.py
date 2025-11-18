# Generated manually to remove restaurant field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        # Remove restaurant_id column and its constraint
        migrations.RunSQL(
            sql="""
                -- Drop foreign key constraint if exists
                ALTER TABLE menu_menuplan 
                DROP CONSTRAINT IF EXISTS menu_menuplan_restaurant_id_fkey;
                
                -- Drop the column
                ALTER TABLE menu_menuplan 
                DROP COLUMN IF EXISTS restaurant_id;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]


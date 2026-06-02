"""Clear all auto-seeded categories.

Categories are now managed exclusively through the Django admin panel.
After this migration the table is empty — add categories manually.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0007_seed_multilingual_categories"),
    ]

    operations = [
        migrations.RunPython(
            lambda apps, se: apps.get_model("metax", "CategoryModel").objects.all().delete(),
            migrations.RunPython.noop,
        ),
    ]

"""Remove all seeded categories so the admin can define them from scratch."""

from django.db import migrations


def _clear(apps, schema_editor):  # noqa: ANN001
    apps.get_model("metax", "CategoryModel").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0004_remove_category_helper_words"),
    ]

    operations = [
        migrations.RunPython(_clear, migrations.RunPython.noop),
    ]

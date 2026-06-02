from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0003_initial_categories_2026_06_02_0000"),
    ]

    operations = [
        migrations.DeleteModel(name="CategoryHelperWordsModel"),
    ]

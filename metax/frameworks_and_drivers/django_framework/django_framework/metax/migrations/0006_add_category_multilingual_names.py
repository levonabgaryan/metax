from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0005_clear_initial_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="categorymodel",
            name="name_hy",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="categorymodel",
            name="name_ru",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
    ]

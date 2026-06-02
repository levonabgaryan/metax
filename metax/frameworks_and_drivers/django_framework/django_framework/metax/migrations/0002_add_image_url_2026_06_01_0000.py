from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0001_initial_2026_05_06_16_40"),
    ]

    operations = [
        migrations.AddField(
            model_name="discountedproductmodel",
            name="image_url",
            field=models.URLField(blank=True, max_length=2048, null=True),
        ),
    ]

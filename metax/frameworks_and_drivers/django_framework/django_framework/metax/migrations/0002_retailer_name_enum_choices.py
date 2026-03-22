# Generated manually — restricts retailer.name to RetailersNames values.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("metax", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="retailermodel",
            name="name",
            field=models.CharField(
                choices=[("yerevan-city", "yerevan-city"), ("sas-am", "sas-am")],
                max_length=64,
                unique=True,
            ),
        ),
    ]

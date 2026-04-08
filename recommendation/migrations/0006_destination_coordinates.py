from django.db import migrations, models
from django.core.validators import MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("recommendation", "0005_travelpackage_distance_km"),
    ]

    operations = [
        migrations.AddField(
            model_name="destination",
            name="latitude",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[MinValueValidator(-90), MaxValueValidator(90)],
            ),
        ),
        migrations.AddField(
            model_name="destination",
            name="longitude",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[MinValueValidator(-180), MaxValueValidator(180)],
            ),
        ),
    ]

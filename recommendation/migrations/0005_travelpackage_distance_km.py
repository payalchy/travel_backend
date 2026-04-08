from django.db import migrations, models
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("recommendation", "0004_packageitinerary_alter_destination_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="travelpackage",
            name="distance_km",
            field=models.FloatField(default=0, validators=[MinValueValidator(0)]),
        ),
    ]

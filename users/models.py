from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class TravelStyle(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class UserProfile(models.Model):

    SEASON_CHOICES = [
        ("summer", "Summer"),
        ("rainy", "Rainy"),
        ("spring", "Spring"),
        ("autumn", "Autumn"),
        ("winter", "Winter"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    #  MUST BE POSITIVE (>0)
    budget_preference = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.01)]
    )

    #  MULTI-SELECT
    preferred_travel_style = models.ManyToManyField(TravelStyle)

    #  ONLY POSITIVE VALUES
    preferred_duration = models.PositiveIntegerField(default=1)

    #  DROPDOWN (NO RANDOM INPUT)
    preferred_season = models.CharField(
        max_length=20,
        choices=SEASON_CHOICES,
        default="summer",
    )

    def __str__(self):
        return self.user.username
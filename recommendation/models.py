from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Destination(models.Model):
    pName = models.CharField(max_length=200)
    province = models.CharField(max_length=50, null=True, blank=True)

    culture = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    adventure = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    wildlife = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    sightseeing = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    history = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    tags = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('pName', 'province')

    def __str__(self):
        return f"{self.pName} ({self.province})"
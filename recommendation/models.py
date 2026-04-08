from django.db import models

class Destination(models.Model):
    name = models.CharField(max_length=100)
    cost = models.FloatField()
    duration = models.IntegerField()

    culture = models.IntegerField(default=0)
    adventure = models.IntegerField(default=0)
    wildlife = models.IntegerField(default=0)
    sightseeing = models.IntegerField(default=0)
    history = models.IntegerField(default=0)

    def __str__(self):
        return self.name
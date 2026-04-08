from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models.functions import Lower

class Destination(models.Model):
    pName = models.CharField(max_length=200)
    province = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

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
        constraints = [
            models.UniqueConstraint(
                Lower('pName'),
                Lower('province'),
                name='unique_destination_case_insensitive'
            )
        ]
    
    def __str__(self):
        return f"{self.pName} ({self.province})"

def validate_image(image):
    if image.size > 2 * 1024 * 1024:  
        raise ValidationError("Image size should not exceed 2MB")
class TravelPackage(models.Model):
    TRANSPORT_CHOICES = [
        ('car', 'Car'),
        ('jeep', 'Jeep'),
        ('bus', 'Bus'),
        ('flight', 'Flight'),
        ('bike', 'Bike'),
    ]

    PACKAGE_TYPE_CHOICES = [
        ('tour', 'Tour'),
        ('hiking', 'Hiking'),
        ('sightseeing', 'Sightseeing'),
        ('adventure', 'Adventure'),
    ]
    name = models.CharField(max_length=200,default="")

    transport_mode = models.CharField(
        max_length=20,
        choices=TRANSPORT_CHOICES,
        default='bus'
    )

    package_type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        default='tour'
    )

    
    start_location = models.ForeignKey('Destination',on_delete=models.SET_NULL,null=True,related_name='start_packages')
    end_location = models.ForeignKey('Destination',on_delete=models.SET_NULL,null=True,related_name='end_packages')
    budget = models.FloatField(validators=[MinValueValidator(0)])
    distance_km = models.FloatField(validators=[MinValueValidator(0)], default=0)
    number_of_travelers = models.IntegerField(validators=[MinValueValidator(1)],default=1)
    image = models.ImageField(upload_to='packages/', validators=[validate_image],null=True, blank=True)
    description = models.TextField(default="")
    days = models.IntegerField(validators=[MinValueValidator(1)],default=1)

    def __str__(self):
        return self.name

class PackageItinerary(models.Model):
    package = models.ForeignKey(TravelPackage,on_delete=models.CASCADE,related_name='itinerary')
    day_number = models.IntegerField()
    destination = models.ForeignKey('Destination', on_delete=models.CASCADE)
    description = models.TextField(default="")

    def clean(self):
        if self.day_number > self.package.days:
            raise ValidationError("Day exceeds package duration")

    class Meta:
        unique_together = ('package', 'day_number','destination')
        ordering = ['day_number']

    def __str__(self):
        return f"{self.package.name} - Day {self.day_number}"



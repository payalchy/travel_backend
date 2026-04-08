from django.contrib import admin
from .models import UserProfile, TravelStyle

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    filter_horizontal = ('preferred_travel_style',)

admin.site.register(TravelStyle)
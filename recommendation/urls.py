from django.urls import path

from .views import DestinationGeocodeAPIView, RecommendationAPIView


urlpatterns = [
    path("recommend/", RecommendationAPIView.as_view(), name="recommend-packages"),
    path("destination/geocode/", DestinationGeocodeAPIView.as_view(), name="destination-geocode"),
]

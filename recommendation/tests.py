from django.urls import reverse
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Destination, TravelPackage


class RecommendationAPITests(APITestCase):
	def setUp(self):
		self.start = Destination.objects.create(pName="Kathmandu", province="Bagmati")
		self.end_1 = Destination.objects.create(
			pName="Pokhara",
			province="Gandaki",
			latitude=28.2096,
			longitude=83.9856,
		)
		self.end_2 = Destination.objects.create(
			pName="Chitwan",
			province="Bagmati",
			latitude=27.5291,
			longitude=84.3542,
		)
		self.end_3 = Destination.objects.create(
			pName="Lumbini",
			province="Lumbini",
			latitude=27.4845,
			longitude=83.2760,
		)

		self.end_1.culture = 4.0
		self.end_1.adventure = 4.8
		self.end_1.wildlife = 3.0
		self.end_1.sightseeing = 4.6
		self.end_1.history = 3.5
		self.end_1.save()

		self.end_2.culture = 3.5
		self.end_2.adventure = 3.0
		self.end_2.wildlife = 4.9
		self.end_2.sightseeing = 3.4
		self.end_2.history = 2.8
		self.end_2.save()

		self.end_3.culture = 4.7
		self.end_3.adventure = 2.6
		self.end_3.wildlife = 2.5
		self.end_3.sightseeing = 4.2
		self.end_3.history = 4.9
		self.end_3.save()

		TravelPackage.objects.create(
			name="Balanced Adventure",
			package_type="adventure",
			transport_mode="bus",
			start_location=self.start,
			end_location=self.end_1,
			budget=20000,
			distance_km=210,
			days=4,
			number_of_travelers=2,
			description="A balanced route",
		)
		TravelPackage.objects.create(
			name="Budget Tour",
			package_type="tour",
			transport_mode="bus",
			start_location=self.start,
			end_location=self.end_2,
			budget=12000,
			distance_km=155,
			days=3,
			number_of_travelers=2,
			description="Affordable package",
		)
		TravelPackage.objects.create(
			name="Long Scenic",
			package_type="sightseeing",
			transport_mode="car",
			start_location=self.start,
			end_location=self.end_3,
			budget=32000,
			distance_km=360,
			days=6,
			number_of_travelers=2,
			description="Long scenic package",
		)

	def test_recommendation_api_returns_ranked_top_n(self):
		url = reverse("recommend-packages")
		payload = {
			"budget": 18000,
			"distance": 200,
			"duration": 4,
			"travel_type": "adventure",
			"user_latitude": 27.7172,
			"user_longitude": 85.3240,
			"k": 3,
			"top_n": 2,
			"alpha": 0.5,
			"beta": 0.3,
			"gamma": 0.2,
		}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["package_count"], 2)
		self.assertEqual(len(response.data["package_results"]), 2)

		first = response.data["package_results"][0]
		second = response.data["package_results"][1]
		self.assertGreaterEqual(first["final_score"], second["final_score"])

	def test_recommendation_api_contains_formula_components(self):
		url = reverse("recommend-packages")
		payload = {
			"budget": 15000,
			"distance": 160,
			"duration": 3,
			"user_latitude": 27.7172,
			"user_longitude": 85.3240,
			"k": 3,
			"top_n": 3,
		}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		sample = response.data["package_results"][0]
		self.assertIn("cps", sample)
		self.assertIn("distance_score", sample)
		self.assertIn("computed_distance_km", sample)
		self.assertIn("cost_efficiency", sample)
		self.assertIn("time_efficiency", sample)
		self.assertIn("final_score", sample)

	def test_destination_preferences_are_returned_and_ranked(self):
		url = reverse("recommend-packages")
		payload = {
			"budget": 20000,
			"distance": 220,
			"duration": 4,
			"travel_type": "adventure",
			"user_latitude": 27.7172,
			"user_longitude": 85.3240,
			"culture": 4.2,
			"adventure": 5.0,
			"wildlife": 3.0,
			"sightseeing": 4.5,
			"history": 3.2,
			"k": 3,
			"top_n": 3,
			"destination_top_n": 2,
		}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["destination_count"], 2)
		self.assertEqual(len(response.data["destination_results"]), 2)

		destination_sample = response.data["destination_results"][0]
		self.assertIn("distance_km", destination_sample)
		self.assertIn("preference_score", destination_sample)
		self.assertIn("geo_score", destination_sample)
		self.assertIn("package_support_score", destination_sample)
		self.assertIn("final_score", destination_sample)

	@patch("recommendation.views.urlopen")
	def test_destination_geocode_endpoint_returns_coordinates(self, mock_urlopen):
		mock_response = Mock()
		mock_response.read.return_value = (
			b'[{"lat":"27.7172","lon":"85.3240","display_name":"Kathmandu, Nepal"}]'
		)
		mock_urlopen.return_value.__enter__.return_value = mock_response

		url = reverse("destination-geocode")
		response = self.client.get(url, {"name": "Kathmandu"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["name"], "Kathmandu")
		self.assertEqual(response.data["latitude"], 27.7172)
		self.assertEqual(response.data["longitude"], 85.324)

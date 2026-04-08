from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.shortcuts import render
from django.urls import reverse
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, TravelPackage, PackageItinerary
from .engine import recommend_destinations, recommend_packages


@staff_member_required
def admin_dashboard(request):
    recent_packages = (
        TravelPackage.objects.select_related("start_location", "end_location")
        .order_by("-id")[:8]
    )

    context = {
        **admin.site.each_context(request),  # keeps admin header/sidebar context
        "total_destinations": Destination.objects.count(),
        "total_packages": TravelPackage.objects.count(),
        "total_itineraries": PackageItinerary.objects.count(),
        "recent_packages": recent_packages,
        "destination_changelist_url": reverse(
            "admin:recommendation_destination_changelist"
        ),
        "package_changelist_url": reverse(
            "admin:recommendation_travelpackage_changelist"
        ),
        "itinerary_changelist_url": reverse(
            "admin:recommendation_packageitinerary_changelist"
        ),
    }
    return render(request, "admin/custom_dashboard.html", context)


class RecommendationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data or {}

        user_context = {
            "budget": payload.get("budget", 0),
            "distance": payload.get("distance", 0),
            "duration": payload.get("duration", 1),
            "travel_type": payload.get("travel_type", ""),
            "user_latitude": payload.get("user_latitude"),
            "user_longitude": payload.get("user_longitude"),
        }

        user_destination_preferences = {
            "culture": payload.get("culture", 0),
            "adventure": payload.get("adventure", 0),
            "wildlife": payload.get("wildlife", 0),
            "sightseeing": payload.get("sightseeing", 0),
            "history": payload.get("history", 0),
        }

        preference_weights = payload.get("preference_weights") or {
            "budget": 0.3,
            "distance": 0.3,
            "duration": 0.2,
            "travel_type": 0.2,
        }
        context_weights = payload.get("context_weights") or {
            "budget": 0.4,
            "distance": 0.3,
            "duration": 0.3,
        }
        destination_weights = payload.get("destination_weights") or {
            "culture": 0.2,
            "adventure": 0.2,
            "wildlife": 0.2,
            "sightseeing": 0.2,
            "history": 0.2,
        }

        k = payload.get("k", 5)
        top_n = payload.get("top_n", 5)
        destination_top_n = payload.get("destination_top_n", top_n)
        alpha = payload.get("alpha", 0.4)
        beta = payload.get("beta", 0.4)
        gamma = payload.get("gamma", 0.2)
        destination_alpha = payload.get("destination_alpha", 0.5)
        destination_beta = payload.get("destination_beta", 0.3)
        destination_gamma = payload.get("destination_gamma", 0.2)

        packages = TravelPackage.objects.select_related("start_location", "end_location").all()
        destinations = Destination.objects.all()

        ranked = recommend_packages(
            user_context=user_context,
            packages=packages,
            k=k,
            top_n=top_n,
            preference_weights=preference_weights,
            context_weights=context_weights,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
        )

        data = []
        for item in ranked:
            package = item.package
            data.append(
                {
                    "package_id": package.id,
                    "name": package.name,
                    "package_type": package.package_type,
                    "transport_mode": package.transport_mode,
                    "budget": float(package.budget),
                    "computed_distance_km": round(item.computed_distance_km, 6),
                    "duration_days": int(package.days),
                    "start_location": package.start_location.pName if package.start_location else None,
                    "end_location": package.end_location.pName if package.end_location else None,
                    "cps": round(item.cps, 6),
                    "distance_score": round(item.distance, 6),
                    "cost_efficiency": round(item.cost_efficiency, 6),
                    "time_efficiency": round(item.time_efficiency, 6),
                    "final_score": round(item.final_score, 6),
                }
            )

        destination_ranked = recommend_destinations(
            user_destination_preferences=user_destination_preferences,
            user_context=user_context,
            destinations=destinations,
            ranked_packages=ranked,
            destination_top_n=destination_top_n,
            destination_weights=destination_weights,
            destination_alpha=destination_alpha,
            destination_beta=destination_beta,
            destination_gamma=destination_gamma,
        )

        destination_data = []
        for item in destination_ranked:
            destination = item.destination
            destination_data.append(
                {
                    "destination_id": destination.id,
                    "name": destination.pName,
                    "province": destination.province,
                    "latitude": destination.latitude,
                    "longitude": destination.longitude,
                    "culture": destination.culture,
                    "adventure": destination.adventure,
                    "wildlife": destination.wildlife,
                    "sightseeing": destination.sightseeing,
                    "history": destination.history,
                    "distance_km": round(item.distance_km, 6),
                    "preference_score": round(item.preference_score, 6),
                    "geo_score": round(item.geo_score, 6),
                    "package_support_score": round(item.package_support_score, 6),
                    "final_score": round(item.final_score, 6),
                }
            )

        return Response(
            {
                "package_count": len(data),
                "destination_count": len(destination_data),
                "package_results": data,
                "destination_results": destination_data,
            },
            status=status.HTTP_200_OK,
        )


class DestinationGeocodeAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        destination_name = request.query_params.get("name", "").strip()
        if not destination_name:
            return Response(
                {"detail": "Query parameter 'name' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = f"{destination_name}, Nepal"
        params = urlencode({"q": query, "format": "json", "limit": 1})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        req = Request(url, headers={"User-Agent": "travel-backend/1.0"})

        try:
            with urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return Response(
                {"detail": "Unable to fetch location right now."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not payload:
            return Response(
                {"detail": "No location found for this destination in Nepal."},
                status=status.HTTP_404_NOT_FOUND,
            )

        first = payload[0]
        return Response(
            {
                "name": destination_name,
                "latitude": float(first.get("lat")),
                "longitude": float(first.get("lon")),
                "display_name": first.get("display_name"),
            },
            status=status.HTTP_200_OK,
        )
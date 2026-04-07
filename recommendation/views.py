from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import reverse

from .models import Destination, TravelPackage, PackageItinerary


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
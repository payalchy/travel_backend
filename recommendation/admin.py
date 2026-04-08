from django.contrib import admin
from django.contrib import messages
from django.apps import apps
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import Truncator
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Destination, TravelPackage, PackageItinerary

admin.site.site_header = "Travel Management Admin"
admin.site.site_title = "Travel Admin"
admin.site.index_title = "Dashboard"

_default_each_context = admin.site.each_context


def _dashboard_each_context(request):
    context = _default_each_context(request)
    user_model = get_user_model()
    booking_model = next(
        (model for model in apps.get_models() if model.__name__.lower() == "booking"),
        None,
    )

    module_cards = [
        {
            "title": "Destinations",
            "count": Destination.objects.count(),
            "url": reverse("admin:recommendation_destination_changelist"),
            "add_url": reverse("admin:recommendation_destination_add"),
        },
        {
            "title": "Packages",
            "count": TravelPackage.objects.count(),
            "url": reverse("admin:recommendation_travelpackage_changelist"),
            "add_url": reverse("admin:recommendation_travelpackage_add"),
        },
        {
            "title": "Users",
            "count": user_model.objects.count(),
            "url": reverse("admin:auth_user_changelist"),
            "add_url": reverse("admin:auth_user_add"),
        },
    ]

    recent_activities = []
    for destination in Destination.objects.order_by("-id")[:4]:
        recent_activities.append(
            {
                "label": "Destination added",
                "detail": f"{destination.pName} ({destination.province or 'N/A'})",
                "url": reverse("admin:recommendation_destination_change", args=[destination.id]),
            }
        )

    for package in TravelPackage.objects.order_by("-id")[:4]:
        recent_activities.append(
            {
                "label": "Package added",
                "detail": package.name,
                "url": reverse("admin:recommendation_travelpackage_change", args=[package.id]),
            }
        )

    for account in user_model.objects.order_by("-id")[:4]:
        recent_activities.append(
            {
                "label": "User signup",
                "detail": account.get_username(),
                "url": reverse("admin:auth_user_change", args=[account.id]),
            }
        )

    context.update(
        {
            "total_destinations": Destination.objects.count(),
            "total_packages": TravelPackage.objects.count(),
            "total_users": user_model.objects.count(),
            "total_bookings": booking_model.objects.count() if booking_model else 0,
            "module_cards": module_cards,
            "recent_activities": recent_activities[:12],
        }
    )
    return context


admin.site.each_context = _dashboard_each_context

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "destination_summary",
        "province_badge",
        "culture_score",
        "adventure_score",
        "wildlife_score",
        "sightseeing_score",
        "history_score",
        "ratings_summary",
        "tags_summary",
        "quick_edit",
    )
    list_display_links = ("id", "destination_summary")
    search_fields = ("pName", "province", "tags")
    list_filter = ("province",)
    ordering = ("pName",)
    list_per_page = 50
    readonly_fields = ("coordinate_tools",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:destination_id>/autofill-coordinates/",
                self.admin_site.admin_view(self.autofill_coordinates_view),
                name="recommendation_destination_autofill_coordinates",
            ),
        ]
        return custom_urls + urls

    def autofill_coordinates_view(self, request, destination_id):
        destination = self.get_object(request, str(destination_id))
        if destination is None:
            self.message_user(request, "Destination not found.", level=messages.ERROR)
            return redirect(reverse("admin:recommendation_destination_changelist"))

        if not destination.pName:
            self.message_user(request, "Destination name is required for geocoding.", level=messages.ERROR)
            return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

        query = f"{destination.pName}, Nepal"
        params = urlencode({"q": query, "format": "json", "limit": 1})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        request_obj = Request(url, headers={"User-Agent": "travel-backend-admin/1.0"})

        try:
            with urlopen(request_obj, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            self.message_user(request, "Could not fetch coordinates right now.", level=messages.ERROR)
            return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

        if not payload:
            self.message_user(request, "No Nepal location found for this destination.", level=messages.WARNING)
            return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

        first = payload[0]
        destination.latitude = float(first.get("lat"))
        destination.longitude = float(first.get("lon"))
        destination.save(update_fields=["latitude", "longitude"])

        self.message_user(request, "Coordinates updated successfully.", level=messages.SUCCESS)
        return redirect(reverse("admin:recommendation_destination_change", args=[destination.id]))

    @admin.display(description="Coordinate Tools")
    def coordinate_tools(self, obj):
        if obj is None or obj.id is None:
            return "Save destination first, then use auto-fill."
        url = reverse("admin:recommendation_destination_autofill_coordinates", args=[obj.id])
        return format_html('<a class="button" href="{}">Auto Fill Coordinates</a>', url)

    @admin.display(description="Destination", ordering="pName")
    def destination_summary(self, obj):
        return format_html(
            '<div class="tm-admin-title">{}</div>'
            '<div class="tm-admin-sub">ID #{}</div>',
            obj.pName,
            obj.id,
        )

    @admin.display(description="Province", ordering="province")
    def province_badge(self, obj):
        label = obj.province or "N/A"
        return format_html('<span class="tm-admin-badge">{}</span>', label)

    @admin.display(description="Rating")
    def ratings_summary(self, obj):
        values = [obj.culture, obj.adventure, obj.wildlife, obj.sightseeing, obj.history]
        filtered = [float(value) for value in values if value is not None]
        average = round(sum(filtered) / len(filtered), 1) if filtered else 0
        return format_html('<span class="tm-admin-rating">{}/5</span>', average)

    @admin.display(description="Culture", ordering="culture")
    def culture_score(self, obj):
        return f"{obj.culture:.1f}" if obj.culture is not None else "-"

    @admin.display(description="Adventure", ordering="adventure")
    def adventure_score(self, obj):
        return f"{obj.adventure:.1f}" if obj.adventure is not None else "-"

    @admin.display(description="Wildlife", ordering="wildlife")
    def wildlife_score(self, obj):
        return f"{obj.wildlife:.1f}" if obj.wildlife is not None else "-"

    @admin.display(description="Sightseeing", ordering="sightseeing")
    def sightseeing_score(self, obj):
        return f"{obj.sightseeing:.1f}" if obj.sightseeing is not None else "-"

    @admin.display(description="History", ordering="history")
    def history_score(self, obj):
        return f"{obj.history:.1f}" if obj.history is not None else "-"

    @admin.display(description="Tags")
    def tags_summary(self, obj):
        if not obj.tags:
            return "-"
        return Truncator(obj.tags).chars(36)

    @admin.display(description="Actions")
    def quick_edit(self, obj):
        url = reverse("admin:recommendation_destination_change", args=[obj.id])
        return format_html('<a class="tm-admin-edit-btn" href="{}">Edit</a>', url)

class PackageItineraryInline(admin.TabularInline):
    model = PackageItinerary
    extra = 0
    autocomplete_fields = ["destination"]
    can_delete = True
    ordering = ("day_number",)

@admin.register(TravelPackage)
class TravelPackageAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "package_summary",
        "package_type_badge",
        "budget_display",
        "duration_display",
        "route_summary",
        "quick_edit",
    )
    list_display_links = ("package_summary",)
    search_fields = ("name", "package_type", "transport_mode")
    list_filter = ("package_type", "transport_mode")
    autocomplete_fields = ["start_location", "end_location"]
    list_select_related = ("start_location", "end_location")
    inlines = [PackageItineraryInline]
    save_on_top = True

    def get_exclude(self, request, obj=None):
        # Hide distance_km only on the add form.
        if obj is None:
            return ("distance_km",)
        return super().get_exclude(request, obj)

    @admin.display(description="Package")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" alt="{}" class="tm-admin-thumb" style="width: 84px; height: 52px; max-width: 84px; max-height: 52px; object-fit: cover;"/>',
                obj.image.url,
                obj.name,
            )
        return format_html('<div class="tm-admin-thumb tm-admin-thumb-empty">{}</div>', "No Image")

    @admin.display(description="Details", ordering="name")
    def package_summary(self, obj):
        transport = obj.get_transport_mode_display() if obj.transport_mode else "-"
        return format_html(
            '<div class="tm-admin-title">{}</div>'
            '<div class="tm-admin-sub">{}</div>',
            obj.name,
            transport,
        )

    @admin.display(description="Type", ordering="package_type")
    def package_type_badge(self, obj):
        return format_html('<span class="tm-admin-badge">{}</span>', obj.get_package_type_display())

    @admin.display(description="Budget", ordering="budget")
    def budget_display(self, obj):
        value = float(obj.budget or 0)
        return f"NPR {value:,.0f}"

    @admin.display(description="Duration", ordering="days")
    def duration_display(self, obj):
        return f"{obj.days} day{'s' if obj.days != 1 else ''}"

    @admin.display(description="Route")
    def route_summary(self, obj):
        start = obj.start_location.pName if obj.start_location else "-"
        end = obj.end_location.pName if obj.end_location else "-"
        return format_html(
            '<div class="tm-admin-sub">{}</div>'
            '<div class="tm-admin-sub">{}</div>',
            start,
            end,
        )

    @admin.display(description="Actions")
    def quick_edit(self, obj):
        url = reverse("admin:recommendation_travelpackage_change", args=[obj.id])
        return format_html('<a class="tm-admin-edit-btn" href="{}">Edit</a>', url)
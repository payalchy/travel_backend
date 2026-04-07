from django.contrib import admin
from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import Truncator

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
        "ratings_summary",
        "tags_summary",
        "quick_edit",
    )
    list_display_links = ("id", "destination_summary")
    search_fields = ("pName", "province", "tags")
    list_filter = ("province",)
    ordering = ("pName",)
    list_per_page = 50

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

    @admin.display(description="Package")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" alt="{}" class="tm-admin-thumb"/>',
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
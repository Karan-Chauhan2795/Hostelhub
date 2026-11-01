from django.contrib import admin
from .models import HostelEvent


@admin.register(HostelEvent)
class HostelEventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "event_type",
        "audience",
        "event_date",
        "event_time",
        "end_time",
        "location",
        "is_recurring_daily",
        "created_by",
    )
    list_filter = ("event_type", "audience", "is_recurring_daily", "event_date")
    search_fields = ("title", "location", "description")
    ordering = ("event_date", "event_time")

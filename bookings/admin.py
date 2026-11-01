from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "room", "status", "requested_at")
    list_filter = ("status", "requested_at")
    search_fields = ("student__user__username", "student__roll_number", "room__number", "notes")
    ordering = ("-requested_at",)


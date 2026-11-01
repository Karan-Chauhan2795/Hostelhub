from django.contrib import admin

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("number", "room_type", "capacity", "monthly_fee", "created_at")
    list_filter = ("room_type", "capacity", "created_at")
    search_fields = ("number",)
    ordering = ("number",)


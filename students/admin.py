from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_number", "user", "course", "room", "created_at")
    list_filter = ("course", "room__room_type", "created_at")
    search_fields = ("roll_number", "user__username", "user__first_name", "user__last_name", "course", "room__number")
    ordering = ("roll_number",)


from django.contrib import admin

from .models import LeaveRequest


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "start_date", "end_date", "status", "created_at")
    list_filter = ("status", "created_at", "start_date")
    search_fields = ("student__user__username", "student__roll_number", "reason")
    ordering = ("-created_at",)


from django.contrib import admin

from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "student", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("subject", "description", "student__user__username", "student__roll_number")
    ordering = ("-created_at",)

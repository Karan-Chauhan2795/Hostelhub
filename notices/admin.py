from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at")
    list_filter = ("created_at", "created_by__role")
    search_fields = ("title", "body", "created_by__username")
    ordering = ("-created_at",)


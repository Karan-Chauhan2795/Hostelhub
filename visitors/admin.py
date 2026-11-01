from django.contrib import admin

from .models import Visitor


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("name", "relation", "student", "phone", "purpose", "check_in", "check_out")
    list_filter = ("check_in", "check_out")
    search_fields = ("name", "relation", "phone", "student__user__username", "student__roll_number", "purpose")
    ordering = ("-check_in",)

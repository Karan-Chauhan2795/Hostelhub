from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class ComplaintManagementView(RoleRequiredMixin, TemplateView):
    template_name = "complaints/complaint_management.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["complaints"] = [
            {"id": "CMP-101", "student": "Aarav Mehta", "issue": "Electrical outlet not working", "status": "In Progress"},
            {"id": "CMP-102", "student": "Sneha Verma", "issue": "Water heater repair", "status": "Resolved"},
            {"id": "CMP-103", "student": "Rajat Kumar", "issue": "Internet connectivity", "status": "Pending"},
        ]
        return context

from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class StudentManagementView(RoleRequiredMixin, TemplateView):
    template_name = "students/student_management.html"
    allowed_roles = ("ADMIN", "WARDEN")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["students"] = [
            {"name": "Aarav Mehta", "roll": "220101", "course": "MCA", "room": "A-101"},
            {"name": "Sneha Verma", "roll": "220102", "course": "MCA", "room": "B-204"},
            {"name": "Rajat Kumar", "roll": "220103", "course": "MCA", "room": "C-305"},
        ]
        return context

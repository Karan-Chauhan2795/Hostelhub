from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import StudentForm
from .models import Student


class StudentManagementView(RoleRequiredMixin, TemplateView):
    template_name = "students/student_management.html"
    allowed_roles = ("ADMIN", "WARDEN")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["students"] = Student.objects.select_related("user", "room")
        return context


class StudentCreateView(RoleRequiredMixin, CreateView):
    template_name = "students/student_create.html"
    form_class = StudentForm
    success_url = reverse_lazy("students:student_management")
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        messages.success(self.request, "Student record added.")
        return super().form_valid(form)


class StudentUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "students/student_update.html"
    form_class = StudentForm
    model = Student
    success_url = reverse_lazy("students:student_management")
    allowed_roles = ("ADMIN", "WARDEN")

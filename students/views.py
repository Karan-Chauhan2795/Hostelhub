from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import StudentForm
from .models import Student


class StudentManagementView(RoleRequiredMixin, ListView):
    model = Student
    template_name = "students/student_management.html"
    allowed_roles = ("ADMIN", "WARDEN")
    paginate_by = 10

    def get_queryset(self):
        students = Student.objects.select_related("user", "room").order_by("-user__is_active", "roll_number")
        query = self.request.GET.get("q", "").strip()
        if query:
            students = students.filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__username__icontains=query)
                | Q(roll_number__icontains=query)
                | Q(course__icontains=query)
                | Q(room__number__icontains=query)
            )
        return students


class StudentCreateView(RoleRequiredMixin, CreateView):
    template_name = "students/student_create.html"
    form_class = StudentForm
    success_url = reverse_lazy("students:student_management")
    allowed_roles = ("ADMIN",)

    def form_valid(self, form):
        messages.success(self.request, "Student record added.")
        return super().form_valid(form)


class StudentUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "students/student_update.html"
    form_class = StudentForm
    model = Student
    success_url = reverse_lazy("students:student_management")
    allowed_roles = ("ADMIN",)


class StudentDeleteView(RoleRequiredMixin, DeleteView):
    model = Student
    template_name = "students/student_confirm_delete.html"
    success_url = reverse_lazy("students:student_management")
    allowed_roles = ("ADMIN",)

    @transaction.atomic
    def form_valid(self, form):
        student = self.get_object()
        user = student.user
        student_name = user.get_full_name() or user.username
        
        # Soft delete: deallocate room and disable user account (is_active=False)
        # This prevents student login while retaining student profile, booking, leave & complaint history in DB.
        student.room = None
        student.save(update_fields=["room"])
        
        user.is_active = False
        user.save(update_fields=["is_active"])
        
        messages.success(
            self.request,
            f"Resident '{student_name}' has been removed from hostel. Account access has been revoked and their history has been archived in the database.",
        )
        return redirect(self.success_url)

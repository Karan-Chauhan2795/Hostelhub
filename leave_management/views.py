from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from .forms import LeaveRequestForm
from .models import LeaveRequest


class LeaveListView(RoleRequiredMixin, ListView):
    model = LeaveRequest
    template_name = "leave_management/leave_list.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")

    def get_queryset(self):
        queryset = LeaveRequest.objects.select_related("student__user")
        return queryset.filter(student__user=self.request.user) if self.request.user.role == "STUDENT" else queryset


class LeaveApplyView(RoleRequiredMixin, CreateView):
    form_class = LeaveRequestForm
    template_name = "leave_management/leave_apply.html"
    success_url = reverse_lazy("leave_management:leave_list")
    allowed_roles = ("STUDENT",)

    def dispatch(self, request, *args, **kwargs):
        self.student = Student.objects.filter(user=request.user).first()
        if self.student is None:
            messages.error(request, "Your student record is not set up yet. Please contact the warden.")
            return redirect("leave_management:leave_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.student
        messages.success(self.request, "Leave request submitted.")
        return super().form_valid(form)


class LeaveDetailView(RoleRequiredMixin, DetailView):
    model = LeaveRequest
    template_name = "leave_management/leave_detail.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")

    def get_queryset(self):
        queryset = LeaveRequest.objects.select_related("student__user")
        return queryset.filter(student__user=self.request.user) if self.request.user.role == "STUDENT" else queryset

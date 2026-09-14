from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from .forms import ComplaintForm, ComplaintStatusForm
from .models import Complaint


class ComplaintManagementView(RoleRequiredMixin, ListView):
    model = Complaint
    template_name = "complaints/complaint_management.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")
    paginate_by = 10

    def get_queryset(self):
        complaints = Complaint.objects.select_related("student__user")
        if self.request.user.role == "STUDENT":
            complaints = complaints.filter(student__user=self.request.user)
        status = self.request.GET.get("status")
        if status in Complaint.Status.values:
            complaints = complaints.filter(status=status)
        query = self.request.GET.get("q", "").strip()
        if query:
            complaints = complaints.filter(Q(subject__icontains=query) | Q(description__icontains=query) | Q(student__user__first_name__icontains=query) | Q(student__user__last_name__icontains=query))
        return complaints


class ComplaintCreateView(RoleRequiredMixin, CreateView):
    form_class = ComplaintForm
    template_name = "complaints/complaint_create.html"
    success_url = reverse_lazy("complaints:complaint_management")
    allowed_roles = ("STUDENT",)

    def dispatch(self, request, *args, **kwargs):
        self.student = Student.objects.filter(user=request.user).first()
        if self.student is None:
            messages.error(request, "Your student record is not set up yet. Please contact the warden.")
            return redirect("complaints:complaint_management")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.student
        messages.success(self.request, "Complaint submitted.")
        return super().form_valid(form)


class ComplaintUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "complaints/complaint_create.html"
    form_class = ComplaintForm
    model = Complaint
    success_url = reverse_lazy("complaints:complaint_management")
    allowed_roles = ("STUDENT",)

    def get_queryset(self):
        return Complaint.objects.filter(student__user=self.request.user)


class ComplaintStatusUpdateView(RoleRequiredMixin, UpdateView):
    model = Complaint
    form_class = ComplaintStatusForm
    http_method_names = ["post"]
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        messages.success(self.request, "Complaint status updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.POST.get("next") or reverse_lazy("complaints:complaint_management")

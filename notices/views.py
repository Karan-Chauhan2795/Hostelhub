from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from accounts.mixins import RoleRequiredMixin
from .forms import NoticeForm
from .models import Notice


class NoticeListView(RoleRequiredMixin, ListView):
    model = Notice
    template_name = "notices/notice_list.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")


class NoticeDetailView(RoleRequiredMixin, DetailView):
    model = Notice
    template_name = "notices/notice_detail.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")


class NoticeCreateView(RoleRequiredMixin, CreateView):
    form_class = NoticeForm
    template_name = "notices/notice_create.html"
    success_url = reverse_lazy("notices:notice_list")
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Notice published.")
        return super().form_valid(form)

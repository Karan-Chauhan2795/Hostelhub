from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import NoticeForm
from .models import Notice


class NoticeListView(RoleRequiredMixin, ListView):
    model = Notice
    template_name = "notices/notice_list.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")
    paginate_by = 10

    def get_queryset(self):
        queryset = Notice.objects.select_related("created_by")
        # Role-based restriction: Students cannot see warden-only notices
        if self.request.user.role == "STUDENT":
            queryset = queryset.exclude(title__startswith="[Warden Only]").exclude(body__startswith="[Warden Only]")

        # Search query
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(title__icontains=query)

        # Admin/Warden filter by audience
        audience = self.request.GET.get("audience", "").strip()
        if self.request.user.role in ("ADMIN", "WARDEN") and audience:
            if audience == "WARDEN_ONLY":
                queryset = queryset.filter(title__startswith="[Warden Only]")
            elif audience == "STUDENTS":
                queryset = queryset.exclude(title__startswith="[Warden Only]")

        return queryset


class NoticeDetailView(RoleRequiredMixin, DetailView):
    model = Notice
    template_name = "notices/notice_detail.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")

    def get_queryset(self):
        queryset = super().get_queryset().select_related("created_by")
        if self.request.user.role == "STUDENT":
            queryset = queryset.exclude(title__startswith="[Warden Only]").exclude(body__startswith="[Warden Only]")
        return queryset



class NoticeCreateView(RoleRequiredMixin, CreateView):
    form_class = NoticeForm
    template_name = "notices/notice_create.html"
    success_url = reverse_lazy("notices:notice_list")
    allowed_roles = ("ADMIN", "WARDEN")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Notice published successfully.")
        return super().form_valid(form)


class NoticeUpdateView(RoleRequiredMixin, UpdateView):
    model = Notice
    form_class = NoticeForm
    template_name = "notices/notice_edit.html"
    success_url = reverse_lazy("notices:notice_list")
    allowed_roles = ("ADMIN", "WARDEN")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        queryset = super().get_queryset()
        # Security: Wardens can only edit notices created by themselves; Admins can edit all
        if self.request.user.role == "WARDEN":
            queryset = queryset.filter(created_by=self.request.user)
        return queryset


    def form_valid(self, form):
        messages.success(self.request, "Notice updated successfully.")
        return super().form_valid(form)


class NoticeDeleteView(RoleRequiredMixin, DeleteView):
    model = Notice
    template_name = "notices/notice_confirm_delete.html"
    success_url = reverse_lazy("notices:notice_list")
    allowed_roles = ("ADMIN", "WARDEN")

    def get_queryset(self):
        queryset = super().get_queryset()
        # Security: Wardens can only delete notices created by themselves; Admins can delete all
        if self.request.user.role == "WARDEN":
            queryset = queryset.filter(created_by=self.request.user)
        return queryset

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Notice deleted successfully.")
        return super().delete(request, *args, **kwargs)



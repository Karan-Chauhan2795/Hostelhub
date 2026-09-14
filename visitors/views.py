from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from accounts.mixins import RoleRequiredMixin
from .forms import VisitorForm
from .models import Visitor


class VisitorListView(RoleRequiredMixin, ListView):
    model = Visitor
    template_name = "visitors/visitor_list.html"
    allowed_roles = ("ADMIN", "WARDEN")
    paginate_by = 10

    def get_queryset(self):
        return Visitor.objects.select_related("student__user")


class VisitorCreateView(RoleRequiredMixin, CreateView):
    form_class = VisitorForm
    template_name = "visitors/visitor_create.html"
    success_url = reverse_lazy("visitors:visitor_list")
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        messages.success(self.request, "Visitor checked in.")
        return super().form_valid(form)


class VisitorHistoryView(VisitorListView):
    template_name = "visitors/visitor_history.html"

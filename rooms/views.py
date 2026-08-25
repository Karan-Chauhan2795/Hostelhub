from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import RoomForm
from .models import Room


class RoomManagementView(RoleRequiredMixin, TemplateView):
    template_name = "rooms/room_management.html"
    allowed_roles = ("ADMIN", "WARDEN")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rooms"] = Room.objects.all()
        return context


class RoomCreateView(RoleRequiredMixin, CreateView):
    template_name = "rooms/room_create.html"
    form_class = RoomForm
    success_url = reverse_lazy("rooms:room_management")
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        messages.success(self.request, "Room added.")
        return super().form_valid(form)


class RoomUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "rooms/room_update.html"
    form_class = RoomForm
    model = Room
    success_url = reverse_lazy("rooms:room_management")
    allowed_roles = ("ADMIN", "WARDEN")

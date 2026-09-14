from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import RoomForm
from .models import Room


class RoomManagementView(RoleRequiredMixin, ListView):
    model = Room
    template_name = "rooms/room_management.html"
    allowed_roles = ("ADMIN", "WARDEN")
    paginate_by = 10

    def get_queryset(self):
        rooms = Room.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            from django.db.models import Q
            rooms = rooms.filter(Q(number__icontains=query) | Q(room_type__icontains=query))
        status = self.request.GET.get("status")
        if status == "VACANT":
            rooms = [room for room in rooms if room.occupied_count == 0]
        elif status == "AVAILABLE":
            rooms = [room for room in rooms if room.occupied_count < room.capacity]
        elif status == "OCCUPIED":
            rooms = [room for room in rooms if room.occupied_count >= room.capacity]
        return rooms


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

from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin


class RoomManagementView(RoleRequiredMixin, TemplateView):
    template_name = "rooms/room_management.html"
    allowed_roles = ("ADMIN", "WARDEN")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rooms"] = [
            {"number": "A-101", "type": "Double", "status": "Occupied", "capacity": "2/2"},
            {"number": "B-204", "type": "Triple", "status": "Partially Occupied", "capacity": "1/2"},
            {"number": "C-305", "type": "Single", "status": "Vacant", "capacity": "0/1"},
        ]
        return context

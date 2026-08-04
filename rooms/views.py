from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import RoomForm
from .models import Room


class RoomListView(ListView):
    model = Room
    template_name = "rooms/room_list.html"


class RoomDetailView(DetailView):
    model = Room
    template_name = "rooms/room_detail.html"


class RoomCreateView(CreateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_create.html"


class RoomUpdateView(UpdateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_update.html"


class RoomAllocationView(TemplateView):
    template_name = "rooms/room_allocation.html"


class RoomTransferView(TemplateView):
    template_name = "rooms/room_transfer.html"

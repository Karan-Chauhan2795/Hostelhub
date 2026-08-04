from django.views.generic import CreateView, ListView, TemplateView

from .forms import BookingForm
from .models import Booking


class BookingListView(ListView):
    model = Booking
    template_name = "bookings/booking_list.html"


class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_create.html"


class BookingHistoryView(TemplateView):
    template_name = "bookings/booking_history.html"

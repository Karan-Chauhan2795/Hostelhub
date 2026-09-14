from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from students.models import Student
from .forms import BookingForm, BookingStatusForm
from .models import Booking


class BookingListView(RoleRequiredMixin, ListView):
    model = Booking
    template_name = "bookings/booking_list.html"
    allowed_roles = ("ADMIN", "WARDEN", "STUDENT")
    paginate_by = 10

    def get_queryset(self):
        queryset = Booking.objects.select_related("student__user", "room")
        if self.request.user.role == "STUDENT":
            queryset = queryset.filter(student__user=self.request.user)
        status = self.request.GET.get("status")
        if status in Booking.Status.values:
            queryset = queryset.filter(status=status)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(room__number__icontains=query) | Q(student__user__first_name__icontains=query) | Q(student__user__last_name__icontains=query) | Q(student__roll_number__icontains=query))
        return queryset


class BookingCreateView(RoleRequiredMixin, CreateView):
    form_class = BookingForm
    template_name = "bookings/booking_create.html"
    success_url = reverse_lazy("bookings:booking_list")
    allowed_roles = ("STUDENT",)

    def dispatch(self, request, *args, **kwargs):
        self.student = Student.objects.filter(user=request.user).first()
        if self.student is None:
            messages.error(request, "Your student record is not set up yet. Please contact the warden.")
            return redirect("bookings:booking_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.student
        messages.success(self.request, "Booking request submitted.")
        return super().form_valid(form)


class BookingHistoryView(BookingListView):
    template_name = "bookings/booking_history.html"


class BookingStatusUpdateView(RoleRequiredMixin, UpdateView):
    """Staff review a request and allocate the requested room on confirmation."""

    model = Booking
    form_class = BookingStatusForm
    http_method_names = ["post"]
    allowed_roles = ("ADMIN", "WARDEN")

    def form_valid(self, form):
        booking = form.instance
        if booking.status == Booking.Status.CONFIRMED:
            room = booking.room
            if booking.student.room_id not in (None, room.id):
                messages.error(self.request, "This resident already has a different room allocation.")
                return redirect(self.get_success_url())
            if booking.student.room_id != room.id and room.occupied_count >= room.capacity:
                messages.error(self.request, "This room is already at capacity.")
                return redirect(self.get_success_url())
            booking.student.room = room
            booking.student.save(update_fields=["room"])
        messages.success(self.request, "Booking status updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.POST.get("next") or reverse_lazy("bookings:booking_list")

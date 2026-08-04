from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.BookingListView.as_view(), name="booking_list"),
    path("create/", views.BookingCreateView.as_view(), name="booking_create"),
    path("history/", views.BookingHistoryView.as_view(), name="booking_history"),
]

from django.urls import path
from rooms import views as room_views
from . import api_views

app_name = "api"

urlpatterns = [
    path("", api_views.APIIndexView.as_view(), name="index"),
    path("rooms/", room_views.RoomListCreateAPIView.as_view(), name="rooms_list_create"),
    path("rooms/<int:pk>/", room_views.RoomDetailAPIView.as_view(), name="rooms_detail"),
    path("students/", api_views.StudentListAPIView.as_view(), name="students_list"),
    path("complaints/", api_views.ComplaintListAPIView.as_view(), name="complaints_list"),
    path("bookings/", api_views.BookingListAPIView.as_view(), name="bookings_list"),
    path("notices/", api_views.NoticeListAPIView.as_view(), name="notices_list"),
    path("leave/", api_views.LeaveRequestListAPIView.as_view(), name="leave_list"),
    path("visitors/", api_views.VisitorListAPIView.as_view(), name="visitors_list"),
]

from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.RoomManagementView.as_view(), name="room_management"),
]

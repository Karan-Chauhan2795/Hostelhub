from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.RoomManagementView.as_view(), name="room_management"),
    path("create/", views.RoomCreateView.as_view(), name="room_create"),
    path("<int:pk>/edit/", views.RoomUpdateView.as_view(), name="room_update"),
    path("api/", views.RoomListCreateAPIView.as_view(), name="room_api_list_create"),
    path("api/<int:pk>/", views.RoomDetailAPIView.as_view(), name="room_api_detail"),
]

from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.RoomListView.as_view(), name="room_list"),
    path("<int:pk>/", views.RoomDetailView.as_view(), name="room_detail"),
    path("create/", views.RoomCreateView.as_view(), name="room_create"),
    path("<int:pk>/update/", views.RoomUpdateView.as_view(), name="room_update"),
    path("allocation/", views.RoomAllocationView.as_view(), name="room_allocation"),
    path("transfer/", views.RoomTransferView.as_view(), name="room_transfer"),
]

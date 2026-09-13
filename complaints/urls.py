from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    path("", views.ComplaintManagementView.as_view(), name="complaint_management"),
    path("create/", views.ComplaintCreateView.as_view(), name="complaint_create"),
    path("<int:pk>/edit/", views.ComplaintUpdateView.as_view(), name="complaint_update"),
    path("<int:pk>/status/", views.ComplaintStatusUpdateView.as_view(), name="complaint_status"),
]

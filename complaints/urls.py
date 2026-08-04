from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    path("", views.ComplaintManagementView.as_view(), name="complaint_management"),
]

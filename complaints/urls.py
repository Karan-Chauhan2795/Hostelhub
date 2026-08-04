from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    path("", views.ComplaintListView.as_view(), name="complaint_list"),
    path("create/", views.ComplaintCreateView.as_view(), name="complaint_create"),
    path("<int:pk>/", views.ComplaintDetailView.as_view(), name="complaint_detail"),
]

from django.urls import path

from . import views

app_name = "leave_management"

urlpatterns = [
    path("", views.LeaveListView.as_view(), name="leave_list"),
    path("apply/", views.LeaveApplyView.as_view(), name="leave_apply"),
    path("<int:pk>/", views.LeaveDetailView.as_view(), name="leave_detail"),
]

from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentManagementView.as_view(), name="student_management"),
    path("create/", views.StudentCreateView.as_view(), name="student_create"),
    path("<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student_update"),
]

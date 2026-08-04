from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.StudentManagementView.as_view(), name="student_management"),
]

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsDashboardView.as_view(), name="reports_dashboard"),
    path("students/", views.StudentReportView.as_view(), name="student_report"),
    path("attendance/", views.AttendanceReportView.as_view(), name="attendance_report"),
    path("rooms/", views.RoomReportView.as_view(), name="room_report"),
    path("complaints/", views.ComplaintReportView.as_view(), name="complaint_report"),
]

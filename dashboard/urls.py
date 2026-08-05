from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.LandingPageView.as_view(), name="landing"),
    path("dashboard/", views.DashboardRedirectView.as_view(), name="home"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("warden/", views.WardenDashboardView.as_view(), name="warden_dashboard"),
    path("student/", views.StudentDashboardView.as_view(), name="student_dashboard"),
]

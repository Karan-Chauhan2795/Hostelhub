from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.LandingPageView.as_view(), name="landing"),
    path("dashboard/", views.DashboardRedirectView.as_view(), name="home"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("warden/", views.WardenDashboardView.as_view(), name="warden_dashboard"),
    path("student/", views.StudentDashboardView.as_view(), name="student_dashboard"),
    # Event Management URLs
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("events/create/", views.EventCreateView.as_view(), name="event_create"),
    path("events/<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_edit"),
    path("events/<int:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),
    path("api/calendar/day-events/", views.CalendarDayEventsApiView.as_view(), name="calendar_day_events_api"),
]

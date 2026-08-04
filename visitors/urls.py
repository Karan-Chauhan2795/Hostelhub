from django.urls import path

from . import views

app_name = "visitors"

urlpatterns = [
    path("", views.VisitorListView.as_view(), name="visitor_list"),
    path("create/", views.VisitorCreateView.as_view(), name="visitor_create"),
    path("history/", views.VisitorHistoryView.as_view(), name="visitor_history"),
]

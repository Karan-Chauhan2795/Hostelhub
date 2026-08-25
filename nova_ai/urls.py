from django.urls import path

from . import views

app_name = "nova_ai"

urlpatterns = [
    path("chat/", views.NovaAIChatView.as_view(), name="chat"),
]

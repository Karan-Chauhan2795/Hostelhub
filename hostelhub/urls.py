from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("students/", include("students.urls", namespace="students")),
    path("rooms/", include("rooms.urls", namespace="rooms")),
    path("bookings/", include("bookings.urls", namespace="bookings")),
    path("complaints/", include("complaints.urls", namespace="complaints")),
    path("leave/", include("leave_management.urls", namespace="leave_management")),
    path("visitors/", include("visitors.urls", namespace="visitors")),
    path("notices/", include("notices.urls", namespace="notices")),
    path("nova-ai/", include("nova_ai.urls", namespace="nova_ai")),
    path("reports/", include("reports.urls", namespace="reports")),
    path("settings/", include("settings_app.urls", namespace="settings_app")),
]

# Development convenience: serve assets directly while DEBUG is enabled.
# In production, the web server/CDN should serve the collected static files.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")

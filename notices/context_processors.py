from notices.models import Notice


def notifications_context(request):
    """Provide real database notices for the global top navigation bell icon."""
    if not request.user.is_authenticated:
        return {
            "navbar_notifications": [],
            "navbar_notifications_count": 0,
        }

    # Fetch latest notices from database
    latest_notices = list(Notice.objects.select_related("created_by").order_by("-created_at")[:5])
    return {
        "navbar_notifications": latest_notices,
        "navbar_notifications_count": len(latest_notices),
    }

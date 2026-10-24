from notices.models import Notice


def notifications_context(request):
    """Provide real database notices for the global top navigation bell icon based on user role."""
    if not request.user.is_authenticated:
        return {
            "navbar_notifications": [],
            "navbar_notifications_count": 0,
            "navbar_latest_notice_id": 0,
        }

    # Fetch latest notices from database filtered by role
    queryset = Notice.objects.select_related("created_by").order_by("-created_at")
    if request.user.role == "STUDENT":
        # Students should NOT see notices marked for warden only
        queryset = queryset.exclude(title__startswith="[Warden Only]").exclude(body__startswith="[Warden Only]")

    latest_notices = list(queryset[:5])
    latest_id = latest_notices[0].pk if latest_notices else 0

    state_components = [f"{n.pk}:{len(n.title)}:{len(n.body)}" for n in latest_notices]
    state_sig = f"{len(queryset)}-{','.join(state_components)}"

    return {
        "navbar_notifications": latest_notices,
        "navbar_notifications_count": len(latest_notices),
        "navbar_latest_notice_id": latest_id,
        "navbar_notices_sig": state_sig,
    }


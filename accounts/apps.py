from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        post_migrate.connect(
            create_demo_users,
            sender=apps.get_app_config("accounts"),
            dispatch_uid="accounts.create_demo_users",
        )


def create_demo_users(sender, **kwargs):
    if sender.name != "accounts":
        return

    from django.db import connection

    from .models import User

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='accounts_user'")
            if not cursor.fetchone():
                return
            cursor.execute("PRAGMA table_info(accounts_user)")
            columns = {row[1] for row in cursor.fetchall()}
            if "role" not in columns:
                return
    except Exception:
        return

    demo_users = [
        ("admin", "admin123", User.Role.ADMIN, "admin@hostelhub.edu", True, True),
        ("warden", "warden123", User.Role.WARDEN, "warden@hostelhub.edu", True, False),
        ("student", "student123", User.Role.STUDENT, "student@hostelhub.edu", False, False),
    ]

    for username, password, role, email, is_staff, is_superuser in demo_users:
        if User.objects.filter(username=username).exists():
            continue

        user = User(
            username=username,
            email=email,
            role=role,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        user.set_password(password)
        user.save()

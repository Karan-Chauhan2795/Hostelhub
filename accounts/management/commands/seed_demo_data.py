from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the standard HostelHub development demo accounts."

    demo_accounts = (
        ("admin", "admin123", "ADMIN"),
        ("warden", "warden123", "WARDEN"),
        ("student", "student123", "STUDENT"),
    )

    def handle(self, *args, **options):
        User = get_user_model()

        for username, password, role_name in self.demo_accounts:
            role = getattr(User.Role, role_name)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "is_active": True},
            )

            changed_fields = []
            if user.role != role:
                user.role = role
                changed_fields.append("role")
            if not user.is_active:
                user.is_active = True
                changed_fields.append("is_active")
            if not user.check_password(password):
                user.set_password(password)
                changed_fields.append("password")

            if changed_fields:
                user.save(update_fields=changed_fields)

            action = "Created" if created else "Verified"
            self.stdout.write(self.style.SUCCESS(f"{action} demo {role_name.lower()} account: {username}"))

        # Keep the demo account immediately usable without overwriting existing data.
        from rooms.models import Room
        from students.models import Student
        from notices.models import Notice

        room, _ = Room.objects.get_or_create(
            number="B-204",
            defaults={"room_type": Room.RoomType.DOUBLE, "capacity": 2, "monthly_fee": 8500},
        )
        student_user = User.objects.get(username="student")
        Student.objects.get_or_create(
            user=student_user,
            defaults={"roll_number": "DEMO-001", "course": "HostelHub Demo", "room": room, "emergency_contact": "HostelHub Support"},
        )
        warden_user = User.objects.get(username="warden")
        Notice.objects.get_or_create(
            title="Welcome to HostelHub",
            defaults={"body": "Use HostelHub to review notices, request leave and contact support.", "created_by": warden_user},
        )
        self.stdout.write(self.style.SUCCESS("Verified demo HostelHub records."))

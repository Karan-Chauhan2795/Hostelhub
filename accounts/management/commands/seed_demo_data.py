import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking
from complaints.models import Complaint
from leave_management.models import LeaveRequest
from notices.models import Notice
from rooms.models import Room
from students.models import Student
from visitors.models import Visitor


class Command(BaseCommand):
    help = "Create or update repeatable HostelHub development demo data."

    accounts = (
        ("admin", "admin@hostelhub.demo", "Admin", "HostelHub", "ADMIN", True),
        ("warden1", "warden1@hostelhub.demo", "Meera", "Shah", "WARDEN", False),
        ("warden2", "warden2@hostelhub.demo", "Arjun", "Mehta", "WARDEN", False),
        ("student1", "student1@hostelhub.demo", "Aarav", "Patel", "STUDENT", False),
        ("student2", "student2@hostelhub.demo", "Diya", "Nair", "STUDENT", False),
        ("student3", "student3@hostelhub.demo", "Kabir", "Singh", "STUDENT", False),
    )

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Set one password for all demo accounts created by this command.")

    def handle(self, *args, **options):
        user_model = get_user_model()
        users = {}
        generated_passwords = []
        requested_password = options.get("password")
        for username, email, first_name, last_name, role_name, is_superuser in self.accounts:
            user, created = user_model.objects.get_or_create(username=username)
            user.email, user.first_name, user.last_name = email, first_name, last_name
            user.role = getattr(user_model.Role, role_name)
            user.phone_number, user.is_active = "+91 90000 00000", True
            user.is_staff = user.is_superuser = is_superuser
            password = requested_password
            if created and not password:
                password = secrets.token_urlsafe(14)
            if password:
                user.set_password(password)
                generated_passwords.append((email, password))
            user.save()
            users[username] = user
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} {role_name.lower()}: {email}"))

        rooms = {}
        for number, room_type, capacity, fee in (
            ("A-101", Room.RoomType.SINGLE, 1, 10500),
            ("A-102", Room.RoomType.DOUBLE, 2, 8500),
            ("B-204", Room.RoomType.DOUBLE, 2, 8500),
            ("C-301", Room.RoomType.TRIPLE, 3, 7200),
        ):
            rooms[number], _ = Room.objects.update_or_create(number=number, defaults={"room_type": room_type, "capacity": capacity, "monthly_fee": fee})

        students = {}
        for username, roll_number, course, room_number, contact in (
            ("student1", "HH2026001", "B.Tech Computer Science", "A-102", "Rohan Patel · +91 90000 10001"),
            ("student2", "HH2026002", "BBA", "B-204", "Anjali Nair · +91 90000 10002"),
            ("student3", "HH2026003", "B.Sc Mathematics", "C-301", "Vikram Singh · +91 90000 10003"),
        ):
            students[username], _ = Student.objects.update_or_create(user=users[username], defaults={"roll_number": roll_number, "course": course, "room": rooms[room_number], "emergency_contact": contact})

        for title, body, author in (
            ("Welcome to the new semester", "Please complete your profile and review the hostel handbook.", "warden1"),
            ("Water maintenance", "Water supply will be briefly interrupted on Saturday morning.", "warden2"),
            ("Common room hours", "The common room is open daily until 10:30 PM.", "warden1"),
        ):
            Notice.objects.update_or_create(title=title, defaults={"body": body, "created_by": users[author]})

        today = timezone.localdate()
        Booking.objects.update_or_create(student=students["student1"], room=rooms["A-102"], defaults={"status": Booking.Status.CONFIRMED, "notes": "Initial confirmed allocation."})
        Booking.objects.update_or_create(student=students["student2"], room=rooms["B-204"], defaults={"status": Booking.Status.PENDING, "notes": "Request awaiting warden review."})
        Booking.objects.update_or_create(student=students["student3"], room=rooms["C-301"], defaults={"status": Booking.Status.CONFIRMED, "notes": "Initial confirmed allocation."})
        LeaveRequest.objects.update_or_create(student=students["student1"], start_date=today + timedelta(days=12), defaults={"end_date": today + timedelta(days=15), "reason": "Family function.", "status": LeaveRequest.Status.PENDING})
        LeaveRequest.objects.update_or_create(student=students["student2"], start_date=today + timedelta(days=20), defaults={"end_date": today + timedelta(days=22), "reason": "Medical appointment.", "status": LeaveRequest.Status.APPROVED})
        for username, subject, description, status in (
            ("student1", "Study lamp needs replacement", "The desk lamp in my room is not working.", Complaint.Status.PENDING),
            ("student2", "Wi-Fi coverage in corridor", "The signal is weak outside the room.", Complaint.Status.IN_PROGRESS),
            ("student3", "Laundry card query", "The laundry card reader did not recognise my card.", Complaint.Status.RESOLVED),
        ):
            Complaint.objects.update_or_create(student=students[username], subject=subject, defaults={"description": description, "status": status})
        for username, name, phone, purpose in (
            ("student1", "Rohan Patel", "+91 90000 10001", "Family visit"),
            ("student2", "Anjali Nair", "+91 90000 10002", "Document drop-off"),
        ):
            Visitor.objects.update_or_create(student=students[username], name=name, defaults={"phone": phone, "purpose": purpose})
        self.stdout.write(self.style.SUCCESS("Demo data is ready; repeated runs update these records without duplicates."))
        if generated_passwords:
            self.stdout.write("Demo passwords set during this run:")
            for email, password in generated_passwords:
                self.stdout.write(f"  {email}: {password}")

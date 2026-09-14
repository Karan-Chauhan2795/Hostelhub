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
    help = "Create a repeatable, non-production HostelHub demo dataset."

    accounts = (
        ("demo_admin", "admin@hostelhub.demo", "Admin", "HostelHub", "ADMIN", True),
        ("demo_warden", "warden@hostelhub.demo", "Meera", "Shah", "WARDEN", False),
        ("demo_student_1", "student1@hostelhub.demo", "Aarav", "Patel", "STUDENT", False),
        ("demo_student_2", "student2@hostelhub.demo", "Diya", "Nair", "STUDENT", False),
        ("demo_student_3", "student3@hostelhub.demo", "Kabir", "Singh", "STUDENT", False),
    )

    def add_arguments(self, parser):
        parser.add_argument("--reset-passwords", action="store_true", help="Generate and print new passwords for existing demo accounts.")

    def handle(self, *args, **options):
        user_model = get_user_model()
        legacy_emails = ("admin@hostelhub.edu", "warden@hostelhub.edu", "student@hostelhub.edu", "admin@hostelhub.demo", *[item[1] for item in self.accounts])
        legacy_usernames = ("admin", "warden1", "warden2", "student1", "student2", "student3")
        # Retain legacy rows for auditability without allowing their duplicate
        # email addresses to intercept an email-based login for a demo account.
        user_model.objects.filter(email__in=legacy_emails).exclude(username__in=[item[0] for item in self.accounts]).update(is_active=False, email="")
        user_model.objects.filter(username__in=legacy_usernames).exclude(username__in=[item[0] for item in self.accounts]).update(is_active=False, email="")
        users, credentials = {}, []
        for username, email, first_name, last_name, role_name, is_superuser in self.accounts:
            user, created = user_model.objects.get_or_create(username=username)
            user.email, user.first_name, user.last_name = email, first_name, last_name
            user.role = getattr(user_model.Role, role_name)
            user.phone_number, user.is_active = "+91 90000 00000", True
            user.is_staff = user.is_superuser = is_superuser
            if created or options["reset_passwords"]:
                password = secrets.token_urlsafe(14)
                user.set_password(password)
                credentials.append((username, email, password))
            user.save()
            users[username] = user
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} {role_name.lower()}: {email}"))
        rooms = {}
        for number, room_type, capacity, fee in (("A-101", Room.RoomType.SINGLE, 1, 10500), ("A-102", Room.RoomType.DOUBLE, 2, 8500), ("B-204", Room.RoomType.DOUBLE, 2, 8500), ("C-301", Room.RoomType.TRIPLE, 3, 7200)):
            rooms[number], _ = Room.objects.update_or_create(number=number, defaults={"room_type": room_type, "capacity": capacity, "monthly_fee": fee})
        students = {}
        for username, roll_number, course, room_number, contact in (("demo_student_1", "HH2026001", "B.Tech Computer Science", "A-102", "Rohan Patel · +91 90000 10001"), ("demo_student_2", "HH2026002", "BBA", "B-204", "Anjali Nair · +91 90000 10002"), ("demo_student_3", "HH2026003", "B.Sc Mathematics", "C-301", "Vikram Singh · +91 90000 10003")):
            student = Student.objects.filter(user=users[username]).first() or Student.objects.filter(roll_number=roll_number).first()
            if student is None:
                student = Student(user=users[username], roll_number=roll_number)
            student.user, student.roll_number = users[username], roll_number
            student.course, student.room, student.emergency_contact = course, rooms[room_number], contact
            student.save()
            students[username] = student
        for title, body in (("Welcome to the new semester", "Please complete your profile and review the hostel handbook."), ("Water maintenance", "Water supply will be briefly interrupted on Saturday morning."), ("Common room hours", "The common room is open daily until 10:30 PM.")):
            Notice.objects.update_or_create(title=title, defaults={"body": body, "created_by": users["demo_warden"]})
        today = timezone.localdate()
        Booking.objects.update_or_create(student=students["demo_student_1"], room=rooms["A-102"], defaults={"status": Booking.Status.CONFIRMED, "notes": "Initial confirmed allocation."})
        Booking.objects.update_or_create(student=students["demo_student_2"], room=rooms["C-301"], defaults={"status": Booking.Status.PENDING, "notes": "Transfer request awaiting review."})
        Booking.objects.update_or_create(student=students["demo_student_3"], room=rooms["C-301"], defaults={"status": Booking.Status.CANCELLED, "notes": "Cancelled test request."})
        LeaveRequest.objects.update_or_create(student=students["demo_student_1"], start_date=today + timedelta(days=12), defaults={"end_date": today + timedelta(days=15), "reason": "Family function.", "status": LeaveRequest.Status.PENDING})
        LeaveRequest.objects.update_or_create(student=students["demo_student_2"], start_date=today + timedelta(days=20), defaults={"end_date": today + timedelta(days=22), "reason": "Medical appointment.", "status": LeaveRequest.Status.APPROVED})
        LeaveRequest.objects.update_or_create(student=students["demo_student_3"], start_date=today + timedelta(days=28), defaults={"end_date": today + timedelta(days=29), "reason": "Academic event.", "status": LeaveRequest.Status.REJECTED})
        for username, subject, description, status in (("demo_student_1", "Study lamp needs replacement", "The desk lamp in my room is not working.", Complaint.Status.PENDING), ("demo_student_2", "Wi-Fi coverage in corridor", "The signal is weak outside the room.", Complaint.Status.IN_PROGRESS), ("demo_student_3", "Laundry card query", "The laundry card reader did not recognise my card.", Complaint.Status.RESOLVED)):
            Complaint.objects.update_or_create(student=students[username], subject=subject, defaults={"description": description, "status": status})
        for username, name, phone, purpose in (("demo_student_1", "Rohan Patel", "+91 90000 10001", "Family visit"), ("demo_student_2", "Anjali Nair", "+91 90000 10002", "Document drop-off")):
            Visitor.objects.update_or_create(student=students[username], name=name, defaults={"phone": phone, "purpose": purpose})
        self.stdout.write(self.style.SUCCESS("Demo data is ready; repeated runs update the same records without duplicates."))
        if credentials:
            self.stdout.write("New demo credentials (shown only for this run):")
            for username, email, password in credentials:
                self.stdout.write(f"  {username} | {email} | {password}")

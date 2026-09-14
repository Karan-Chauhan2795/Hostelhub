import secrets

from django.contrib.auth import get_user_model
from django.test import TestCase

from rooms.models import Room
from students.models import Student


class DashboardDataTests(TestCase):
    def test_admin_dashboard_uses_database_records(self):
        password = secrets.token_urlsafe(16)
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="dashboard_admin", password=password, role=user_model.Role.ADMIN)
        student_user = user_model.objects.create_user(username="dashboard_student", password=password, role=user_model.Role.STUDENT)
        room = Room.objects.create(number="DASH-101", capacity=2)
        Student.objects.create(user=student_user, roll_number="DASH-001", course="Test", room=room)
        self.client.force_login(admin)
        response = self.client.get("/dashboard/admin/")
        self.assertContains(response, "DASH-101")
        self.assertContains(response, "Total Residents")

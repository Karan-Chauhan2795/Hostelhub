from django.contrib.auth import get_user_model
from django.test import TestCase

from rooms.models import Room
from students.models import Student


class DashboardDataTests(TestCase):
    def test_admin_dashboard_uses_database_records(self):
        User = get_user_model()
        admin = User.objects.get(username="admin")
        student_user = User.objects.get(username="student")
        room = Room.objects.create(number="DASH-101", capacity=2)
        Student.objects.create(user=student_user, roll_number="DASH-001", course="Test", room=room)

        self.client.force_login(admin)
        response = self.client.get("/dashboard/admin/")

        self.assertContains(response, "DASH-101")
        self.assertContains(response, "Total Residents")
        self.assertContains(response, "1")

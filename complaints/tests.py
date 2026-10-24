from django.contrib import admin
from django.test import TestCase

from .admin import ComplaintAdmin
from .models import Complaint


class ComplaintAdminTests(TestCase):
    def test_complaint_admin_is_registered(self):
        self.assertIn(Complaint, admin.site._registry)
        model_admin = admin.site._registry[Complaint]
        self.assertIsInstance(model_admin, ComplaintAdmin)

    def test_complaint_admin_list_filter_configured(self):
        model_admin = admin.site._registry[Complaint]
        self.assertIn("status", model_admin.list_filter)
        self.assertIn("created_at", model_admin.list_filter)

    def test_complaint_admin_list_display_and_search_fields(self):
        model_admin = admin.site._registry[Complaint]
        self.assertIn("subject", model_admin.list_display)
        self.assertIn("status", model_admin.list_display)
        self.assertIn("subject", model_admin.search_fields)
        self.assertIn("description", model_admin.search_fields)


class ComplaintModelAndViewsTests(TestCase):
    def setUp(self):
        from accounts.models import User
        from students.models import Student
        from rooms.models import Room

        self.room = Room.objects.create(number="B-101", capacity=2)
        self.user1 = User.objects.create_user(username="student1", password="password123", role="STUDENT")
        self.student1 = Student.objects.create(user=self.user1, roll_number="ST001", room=self.room)

        self.user2 = User.objects.create_user(username="student2", password="password123", role="STUDENT")
        self.student2 = Student.objects.create(user=self.user2, roll_number="ST002", room=self.room)

        self.c1 = Complaint.objects.create(student=self.student1, subject="Issue 1", description="Description 1")
        self.c2 = Complaint.objects.create(student=self.student2, subject="Issue 2", description="Description 2")
        self.c3 = Complaint.objects.create(student=self.student1, subject="Issue 3", description="Description 3")

    def test_student_sequence_number(self):
        self.assertEqual(self.c1.student_sequence_number, 1)
        self.assertEqual(self.c2.student_sequence_number, 1)
        self.assertEqual(self.c3.student_sequence_number, 2)

    def test_student_complaint_management_view(self):
        self.client.login(username="student1", password="password123")
        response = self.client.get("/complaints/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "#1")
        self.assertContains(response, "Description 1")
        self.assertContains(response, "Description 3")
        self.assertNotContains(response, "Description 2")

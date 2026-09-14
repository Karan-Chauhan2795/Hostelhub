import json
import secrets

from django.contrib.auth import get_user_model
from django.test import TestCase

from rooms.models import Room
from students.models import Student


class NovaAccessTests(TestCase):
    def setUp(self):
        password = secrets.token_urlsafe(16)
        user_model = get_user_model()
        self.student_user = user_model.objects.create_user(username="nova_student", password=password, role=user_model.Role.STUDENT)
        self.admin_user = user_model.objects.create_user(username="nova_admin", password=password, role=user_model.Role.ADMIN)
        room = Room.objects.create(number="TEST-101", capacity=2)
        Student.objects.create(user=self.student_user, roll_number="TEST-001", course="Test", room=room)

    def test_nova_is_rendered_only_for_students(self):
        self.client.force_login(self.student_user)
        self.assertContains(self.client.get("/student/"), "data-nova")
        self.client.force_login(self.admin_user)
        self.assertNotContains(self.client.get("/dashboard/admin/"), "data-nova")

    def test_nova_rejects_unrelated_questions_without_provider_access(self):
        self.client.force_login(self.student_user)
        response = self.client.post("/nova-ai/chat/", data=json.dumps({"message": "What is the capital of France?"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("HostelHub", response.json()["reply"])

    def test_nova_endpoint_rejects_non_students(self):
        self.client.force_login(self.admin_user)
        response = self.client.post("/nova-ai/chat/", data=json.dumps({"message": "hostel rules"}), content_type="application/json")
        self.assertEqual(response.status_code, 302)

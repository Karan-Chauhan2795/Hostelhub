from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rooms.models import Room
from students.models import Student
from visitors.models import Visitor

User = get_user_model()


class VisitorTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="testadmin",
            password="password123",
            role="ADMIN",
            first_name="Admin",
            last_name="User"
        )
        self.warden_user = User.objects.create_user(
            username="testwarden",
            password="password123",
            role="WARDEN",
            first_name="Test",
            last_name="Warden"
        )
        self.student_user = User.objects.create_user(
            username="teststudent",
            password="password123",
            role="STUDENT",
            first_name="Rohan",
            last_name="Verma"
        )
        self.student_user_other = User.objects.create_user(
            username="otherstudent",
            password="password123",
            role="STUDENT",
            first_name="Anita",
            last_name="Sharma"
        )
        self.room = Room.objects.create(number="B-101", capacity=2)
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="HH2026999",
            course="Computer Engineering",
            room=self.room
        )
        self.student_other = Student.objects.create(
            user=self.student_user_other,
            roll_number="HH2026888",
            course="Electronics",
            room=self.room
        )

    def test_visitor_create_with_relation(self):
        self.client.login(username="testwarden", password="password123")
        create_url = reverse("visitors:visitor_create")
        response = self.client.post(create_url, {
            "student": self.student.pk,
            "name": "Suresh Verma",
            "relation": "Father",
            "phone": "+91 9876543210",
            "purpose": "Bringing winter clothes and medical check-up"
        })
        self.assertEqual(response.status_code, 302)
        visitor = Visitor.objects.filter(name="Suresh Verma").first()
        self.assertIsNotNone(visitor)
        self.assertEqual(visitor.relation, "Father")
        self.assertEqual(visitor.student, self.student)

    def test_visitor_list_view_and_search_by_relation(self):
        Visitor.objects.create(
            student=self.student,
            name="Pooja Verma",
            relation="Sister",
            phone="9876543211",
            purpose="Casual visit"
        )
        self.client.login(username="testwarden", password="password123")
        list_url = reverse("visitors:visitor_list")
        response = self.client.get(list_url, {"q": "Sister"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pooja Verma")
        self.assertContains(response, "Sister")

    def test_admin_can_edit_visitor(self):
        visitor = Visitor.objects.create(
            student=self.student,
            name="Rahul Sharma",
            relation="Friend",
            phone="9876543222",
            purpose="Project discussion"
        )
        self.client.login(username="testadmin", password="password123")
        edit_url = reverse("visitors:visitor_edit", kwargs={"pk": visitor.pk})
        get_response = self.client.get(edit_url)
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(edit_url, {
            "student": self.student.pk,
            "name": "Rahul Sharma (Updated)",
            "relation": "Cousin",
            "phone": "9876543222",
            "purpose": "Corrected purpose"
        })
        self.assertEqual(post_response.status_code, 302)
        visitor.refresh_from_db()
        self.assertEqual(visitor.name, "Rahul Sharma (Updated)")
        self.assertEqual(visitor.relation, "Cousin")

    def test_warden_cannot_edit_visitor(self):
        visitor = Visitor.objects.create(
            student=self.student,
            name="Rahul Sharma",
            relation="Friend",
            phone="9876543222",
            purpose="Project discussion"
        )
        self.client.login(username="testwarden", password="password123")
        edit_url = reverse("visitors:visitor_edit", kwargs={"pk": visitor.pk})
        response = self.client.get(edit_url)
        # RoleRequiredMixin redirects or rejects when role is not in allowed_roles
        self.assertNotEqual(response.status_code, 200)

    def test_student_can_only_see_their_own_visitors(self):
        # Visitor for student 1
        v1 = Visitor.objects.create(
            student=self.student,
            name="Rohan Father",
            relation="Father",
            phone="9876543201",
            purpose="Drop by"
        )
        # Visitor for student 2
        v2 = Visitor.objects.create(
            student=self.student_other,
            name="Anita Mother",
            relation="Mother",
            phone="9876543202",
            purpose="Meet daughter"
        )

        self.client.login(username="teststudent", password="password123")
        list_url = reverse("visitors:visitor_list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rohan Father")
        self.assertNotContains(response, "Anita Mother")

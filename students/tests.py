import secrets
from django.contrib.auth import get_user_model
from django.test import TestCase

from rooms.models import Room
from .models import Student


class StudentManagementAccessTests(TestCase):
    def test_warden_can_access_student_management_list(self):
        user_model = get_user_model()
        warden = user_model.objects.create_user(
            username="warden_tester",
            password=secrets.token_urlsafe(16),
            role=user_model.Role.WARDEN,
        )
        student_user = user_model.objects.create_user(
            username="student_tester",
            password=secrets.token_urlsafe(16),
            role=user_model.Role.STUDENT,
        )
        Student.objects.create(user=student_user, roll_number="R101", course="CS")

        self.client.force_login(warden)
        response = self.client.get("/students/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "student_tester")

    def test_admin_can_delete_student_and_deleted_student_cannot_login(self):
        user_model = get_user_model()
        password = secrets.token_urlsafe(16)
        admin = user_model.objects.create_user(
            username="delete_admin",
            password=password,
            role=user_model.Role.ADMIN,
        )
        student_user = user_model.objects.create_user(
            username="deleted_student",
            password=password,
            role=user_model.Role.STUDENT,
        )
        room = Room.objects.create(number="DEL-101", capacity=2)
        student = Student.objects.create(
            user=student_user,
            roll_number="DEL-001",
            course="Physics",
            room=room,
        )

        # Confirm student could initially log in before deletion
        login_res = self.client.post("/accounts/login/", {"identifier": "deleted_student", "password": password})
        self.assertEqual(login_res.status_code, 302)
        self.client.logout()

        # Admin visits delete confirmation page
        self.client.force_login(admin)
        get_delete = self.client.get(f"/students/{student.pk}/delete/")
        self.assertEqual(get_delete.status_code, 200)
        self.assertContains(get_delete, "Remove Resident From Hostel?")
        self.assertContains(get_delete, "DEL-001")

        # Admin submits deletion
        post_delete = self.client.post(f"/students/{student.pk}/delete/")
        self.assertRedirects(post_delete, "/students/")

        # Verify Student record and User remain in DB for history / audit
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())
        student.refresh_from_db()
        student_user.refresh_from_db()
        self.assertIsNone(student.room)
        self.assertFalse(student_user.is_active)

        # Verify removed resident CANNOT login to the dashboard
        self.client.logout()
        failed_login = self.client.post("/accounts/login/", {"identifier": "deleted_student", "password": password})
        self.assertEqual(failed_login.status_code, 200)
        self.assertContains(failed_login, "Invalid username/email or password.")

        # Verify admin list UI shows 'Vacated / Inactive' and only 'View' action for deleted student
        self.client.force_login(admin)
        list_res = self.client.get("/students/")
        self.assertContains(list_res, "Vacated / Inactive")
        self.assertNotContains(list_res, "Pending Allocation")
        # Edit stay and Delete buttons should not be rendered for the deleted student
        self.assertNotContains(list_res, f"/students/{student.pk}/edit/")
        self.assertNotContains(list_res, f"/students/{student.pk}/delete/")

        # Verify profile view for deleted student does NOT show 'Edit profile' button
        student_profile_res = self.client.get(f"/accounts/profiles/{student_user.pk}/")
        self.assertEqual(student_profile_res.status_code, 200)
        self.assertContains(student_profile_res, "Leaved / Deleted")
        self.assertNotContains(student_profile_res, "Edit profile")
        self.assertNotContains(student_profile_res, f"/accounts/profiles/{student_user.pk}/edit/")

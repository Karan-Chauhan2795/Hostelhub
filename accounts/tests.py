import secrets

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from students.models import Student


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(16)
        self.admin = get_user_model().objects.create_user(username="test_admin", email="test-admin@example.com", password=self.password, role="ADMIN", is_staff=True)
        self.student = get_user_model().objects.create_user(username="test_student", email="test-student@example.com", password=self.password, role="STUDENT")

    def test_login_and_remember_me_session_expiry(self):
        response = self.client.post("/accounts/login/", {"identifier": self.admin.username, "password": self.password, "remember_me": "on"})
        self.assertRedirects(response, "/dashboard/admin/", fetch_redirect_response=False)
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.client.logout()
        response = self.client.post("/accounts/login/", {"identifier": self.student.username, "password": self.password})
        self.assertRedirects(response, "/student/", fetch_redirect_response=False)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_emits_tokenized_link(self):
        response = self.client.post("/accounts/forgot-password/", {"email": self.student.email})
        self.assertRedirects(response, "/accounts/forgot-password/done/", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)


class ProfilePermissionTests(TestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(16)
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username="profile_admin", password=self.password, role=user_model.Role.ADMIN)
        self.student_user = user_model.objects.create_user(username="profile_student", email="student@example.com", password=self.password, role=user_model.Role.STUDENT)
        self.warden = user_model.objects.create_user(username="profile_warden", email="warden@example.com", password=self.password, role=user_model.Role.WARDEN)
        self.student = Student.objects.create(user=self.student_user, roll_number="PROFILE-001", course="Test")

    def test_student_and_warden_can_view_only_their_read_only_profile(self):
        for user in (self.student_user, self.warden):
            self.client.force_login(user)
            self.assertEqual(self.client.get("/accounts/profile/").status_code, 200)
            self.assertContains(self.client.get("/accounts/profile/"), "profile-permissions.css")
            response = self.client.post("/accounts/profile/edit/", {"first_name": "Changed"})
            self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
            self.assertEqual(get_user_model().objects.get(pk=user.pk).first_name, "")
            response = self.client.get(f"/accounts/profiles/{self.student_user.pk}/")
            self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
            self.client.logout()

    def test_admin_can_manage_student_and_warden_profiles(self):
        self.client.force_login(self.admin)
        response = self.client.get("/students/")
        self.assertContains(response, "View profile")
        self.assertContains(response, "Edit profile")
        self.assertContains(self.client.get("/accounts/profiles/wardens/"), self.warden.username)
        self.assertEqual(self.client.get(f"/accounts/profiles/{self.student_user.pk}/").status_code, 200)
        response = self.client.post(
            f"/accounts/profiles/{self.warden.pk}/edit/",
            {"first_name": "Updated", "last_name": "Warden", "email": "updated@example.com", "phone_number": "123"},
        )
        self.assertRedirects(response, f"/accounts/profiles/{self.warden.pk}/", fetch_redirect_response=False)
        self.warden.refresh_from_db()
        self.assertEqual(self.warden.first_name, "Updated")

    def test_warden_cannot_access_student_management(self):
        self.client.force_login(self.warden)
        response = self.client.get("/students/")
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        response = self.client.post(f"/students/{self.student.pk}/edit/", {"roll_number": "CHANGED"})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)

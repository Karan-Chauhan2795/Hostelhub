import secrets

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings


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

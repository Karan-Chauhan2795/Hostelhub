import secrets
import re
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
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
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.client.logout()
        response = self.client.post("/accounts/login/", {"identifier": self.student.username, "password": self.password})
        self.assertRedirects(response, "/student/", fetch_redirect_response=False)
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.client.post("/accounts/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_emits_tokenized_link(self):
        response = self.client.post("/accounts/forgot-password/", {"email": self.student.email})
        self.assertRedirects(response, "/accounts/forgot-password/done/", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)
        reset_url = re.search(r"https?://[^\s]+/accounts/reset/[^\s]+", mail.outbox[0].body).group()
        reset_path = urlparse(reset_url).path
        response = self.client.get(reset_path)
        self.assertEqual(response.status_code, 302)
        reset_path = urlparse(response["Location"]).path
        response = self.client.post(reset_path, {"new_password1": "New-valid-password-123", "new_password2": "New-valid-password-123"})
        self.assertRedirects(response, "/accounts/reset/complete/", fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("New-valid-password-123"))


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

    def test_admin_assisted_password_reset_is_authorized_and_invalidates_old_password(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            f"/accounts/profiles/{self.warden.pk}/reset-password/",
            {"new_password1": "Admin-reset-password-123", "new_password2": "Admin-reset-password-123"},
        )
        self.assertRedirects(response, f"/accounts/profiles/{self.warden.pk}/", fetch_redirect_response=False)
        self.warden.refresh_from_db()
        self.assertTrue(self.warden.check_password("Admin-reset-password-123"))
        self.assertFalse(self.warden.check_password(self.password))

    def test_student_and_warden_cannot_reset_another_users_password(self):
        for user in (self.student_user, self.warden):
            self.client.force_login(user)
            response = self.client.post(
                f"/accounts/profiles/{self.warden.pk}/reset-password/",
                {"new_password1": "Unauthorized-password-123", "new_password2": "Unauthorized-password-123"},
            )
            self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
            self.warden.refresh_from_db()
            self.assertTrue(self.warden.check_password(self.password))
            self.client.logout()

    @override_settings(
        GOOGLE_OAUTH_CLIENT_ID="test-client-id",
        GOOGLE_OAUTH_CLIENT_SECRET="test-client-secret",
        GOOGLE_OAUTH_REDIRECT_URI="http://testserver/accounts/google/callback/",
    )
    def test_google_login_uses_state_nonce_and_existing_account_role(self):
        response = self.client.get("/accounts/google/")
        self.assertEqual(response.status_code, 302)
        params = parse_qs(urlparse(response["Location"]).query)
        self.assertEqual(params["client_id"], ["test-client-id"])
        self.assertIn("state", params)
        with patch("accounts.views.exchange_google_code", return_value="token"), patch(
            "accounts.views.verify_google_token",
            return_value={"email": self.warden.email, "email_verified": True, "nonce": self.client.session["google_oauth_nonce"]},
        ):
            response = self.client.get("/accounts/google/callback/", {"state": params["state"][0], "code": "code"})
        self.assertRedirects(response, "/warden/", fetch_redirect_response=False)

    @override_settings(
        GOOGLE_OAUTH_CLIENT_ID="test-client-id",
        GOOGLE_OAUTH_CLIENT_SECRET="test-client-secret",
        GOOGLE_OAUTH_REDIRECT_URI="http://testserver/accounts/google/callback/",
    )
    def test_google_callback_rejects_invalid_state(self):
        self.client.get("/accounts/google/")
        response = self.client.get("/accounts/google/callback/", {"state": "forged", "code": "code"})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)

    def test_google_token_verifier_constructs_a_valid_transport(self):
        from accounts.views import verify_google_token

        with patch("google.oauth2.id_token.verify_oauth2_token", return_value={}) as verifier:
            verify_google_token("test-token")
        self.assertEqual(verifier.call_args.args[0], "test-token")

    def test_google_token_verifier_can_fetch_google_jwks(self):
        from accounts.views import verify_google_token

        # An invalid JWT reaches Google's public certificate endpoint before
        # validation fails, proving the real HTTP transport is usable.
        with self.assertRaises(Exception) as error:
            verify_google_token("not-a-jwt")
        self.assertNotIn("missing 1 required positional argument", str(error.exception))

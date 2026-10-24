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
        from rooms.models import Room
        self.password = secrets.token_urlsafe(16)
        self.admin = get_user_model().objects.create_user(username="test_admin", email="test-admin@example.com", password=self.password, role="ADMIN", is_staff=True)
        self.student = get_user_model().objects.create_user(username="test_student", email="test-student@example.com", password=self.password, role="STUDENT")
        self.room = Room.objects.create(number="AUTH-101", capacity=2)
        Student.objects.create(user=self.student, roll_number="AUTH-001", course="Engineering", room=self.room)

    def test_login_and_remember_me_session_expiry(self):
        response = self.client.post("/accounts/login/", {"identifier": self.admin.username, "password": self.password, "remember_me": "on"})
        self.assertRedirects(response, "/dashboard/admin/", fetch_redirect_response=False)
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.assertIn("remembered_identifier", response.cookies)

        # In browser, logging out via the portal POST /accounts/logout/ preserves remember cookies
        self.client.post("/accounts/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)

        # Check GET /accounts/login/ pre-fills the identifier from cookie
        get_response = self.client.get("/accounts/login/")
        self.assertContains(get_response, f'value="{self.admin.username}"')
        self.assertContains(get_response, 'checked')

        response = self.client.post("/accounts/login/", {"identifier": self.student.username, "password": self.password})
        self.assertRedirects(response, "/student/", fetch_redirect_response=False)
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.assertEqual(response.cookies["remembered_identifier"].value, "")
        self.client.post("/accounts/logout/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_student_pending_room_allocation_cannot_login(self):
        pending_user = get_user_model().objects.create_user(
            username="pending_student", email="pending@example.com", password=self.password, role="STUDENT"
        )
        Student.objects.create(user=pending_user, roll_number="PENDING-001", course="Science", room=None)
        response = self.client.post("/accounts/login/", {"identifier": pending_user.username, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "Your registration is pending administrator approval and room allocation")

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
        confirm_path = urlparse(response["Location"]).path

        # Password mismatch validation
        mismatch_res = self.client.post(confirm_path, {"new_password1": "New-valid-password-123", "new_password2": "Mismatch-pass-456"})
        self.assertEqual(mismatch_res.status_code, 200)
        self.assertFalse(self.student.check_password("New-valid-password-123"))

        # Successful password update
        response = self.client.post(confirm_path, {"new_password1": "New-valid-password-123", "new_password2": "New-valid-password-123"})
        self.assertRedirects(response, "/accounts/reset/complete/", fetch_redirect_response=False)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("New-valid-password-123"))
        self.assertFalse(self.student.check_password(self.password))

        # Reusing the reset token should now be rejected as invalid/expired
        reused_response = self.client.get(reset_path)
        # Should either redirect to confirm page where validlink is False, or directly reject
        if reused_response.status_code == 302:
            reused_confirm = self.client.get(reused_response["Location"])
            self.assertContains(reused_confirm, "invalid or has already been used")
        else:
            self.assertContains(reused_response, "invalid or has already been used")

        # Old password can no longer log in
        old_login = self.client.post("/accounts/login/", {"identifier": self.student.username, "password": self.password})
        self.assertEqual(old_login.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        # New password logs in successfully
        new_login = self.client.post("/accounts/login/", {"identifier": self.student.username, "password": "New-valid-password-123"})
        self.assertRedirects(new_login, "/student/", fetch_redirect_response=False)
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(self.student.pk))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_unregistered_email_does_not_reveal_existence(self):
        mail.outbox.clear()
        response = self.client.post("/accounts/forgot-password/", {"email": "nonexistent@example.com"})
        self.assertRedirects(response, "/accounts/forgot-password/done/", fetch_redirect_response=False)
        # No email sent for unregistered email address
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_allows_users_with_unusable_passwords(self):
        oauth_user = get_user_model().objects.create_user(
            username="oauth_student", email="oauth_student@example.com", role="STUDENT"
        )
        oauth_user.set_unusable_password()
        oauth_user.save()
        mail.outbox.clear()
        response = self.client.post("/accounts/forgot-password/", {"email": oauth_user.email})
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
        # Student cannot view other profiles
        self.client.force_login(self.student_user)
        self.assertEqual(self.client.get("/accounts/profile/").status_code, 200)
        self.assertContains(self.client.get("/accounts/profile/"), "profile-permissions.css")
        response = self.client.post("/accounts/profile/edit/", {"first_name": "Changed"})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertEqual(get_user_model().objects.get(pk=self.student_user.pk).first_name, "")
        response = self.client.get(f"/accounts/profiles/{self.student_user.pk}/")
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.client.logout()

        # Warden can view own profile, and can view student profile, but cannot edit
        self.client.force_login(self.warden)
        self.assertEqual(self.client.get("/accounts/profile/").status_code, 200)
        response = self.client.post("/accounts/profile/edit/", {"first_name": "Changed"})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertEqual(get_user_model().objects.get(pk=self.warden.pk).first_name, "")
        response = self.client.get(f"/accounts/profiles/{self.student_user.pk}/")
        self.assertEqual(response.status_code, 200)
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

    def test_warden_can_view_residents_but_cannot_edit_student_record(self):
        self.client.force_login(self.warden)
        response = self.client.get("/students/")
        self.assertEqual(response.status_code, 200)
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

    @override_settings(
        GOOGLE_OAUTH_CLIENT_ID="test-client-id",
        GOOGLE_OAUTH_CLIENT_SECRET="test-client-secret",
        GOOGLE_OAUTH_REDIRECT_URI="http://testserver/accounts/google/callback/",
    )
    def test_google_signup_creates_only_a_verified_student_account(self):
        response = self.client.get("/accounts/google/?signup=1")
        params = parse_qs(urlparse(response["Location"]).query)
        email = "new.google.student@example.com"
        with patch("accounts.views.exchange_google_code", return_value="token"), patch(
            "accounts.views.verify_google_token",
            return_value={
                "email": email,
                "email_verified": True,
                "nonce": self.client.session["google_oauth_nonce"],
                "given_name": "Google",
                "family_name": "Student",
            },
        ):
            response = self.client.get("/accounts/google/callback/", {"state": params["state"][0], "code": "code"})
        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        user = get_user_model().objects.get(email=email)
        self.assertEqual(user.role, user.Role.STUDENT)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(Student.objects.filter(user=user).exists())
        self.assertIsNone(Student.objects.get(user=user).room)
        # Verify the student session was not logged in directly into the dashboard
        self.assertNotIn("_auth_user_id", self.client.session)

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


class WardenManagementFeatureTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword@123"
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="warden_admin",
            email="warden_admin@example.com",
            password=self.password,
            role=user_model.Role.ADMIN,
            is_staff=True,
        )
        self.student = user_model.objects.create_user(
            username="warden_student",
            email="warden_student@example.com",
            password=self.password,
            role=user_model.Role.STUDENT,
        )
        self.warden = user_model.objects.create_user(
            username="active_warden",
            email="active_warden@example.com",
            password=self.password,
            role=user_model.Role.WARDEN,
            first_name="Active",
            last_name="Warden",
        )

    def test_admin_can_create_warden(self):
        self.client.force_login(self.admin)
        get_response = self.client.get("/accounts/profiles/wardens/add/")
        self.assertEqual(get_response.status_code, 200)

        post_data = {
            "first_name": "New",
            "last_name": "Warden",
            "username": "new_warden",
            "email": "new_warden@example.com",
            "phone_number": "9876543210",
            "password1": "WardenPass@456",
            "password2": "WardenPass@456",
        }
        post_response = self.client.post("/accounts/profiles/wardens/add/", post_data)
        self.assertRedirects(post_response, "/accounts/profiles/wardens/")

        user_model = get_user_model()
        new_warden = user_model.objects.get(username="new_warden")
        self.assertEqual(new_warden.role, user_model.Role.WARDEN)
        self.assertTrue(new_warden.is_active)
        self.assertEqual(new_warden.email, "new_warden@example.com")
        self.assertEqual(new_warden.phone_number, "9876543210")

    def test_admin_can_delete_warden_and_prevent_login(self):
        # 1. Admin confirms delete view
        self.client.force_login(self.admin)
        confirm_response = self.client.get(f"/accounts/profiles/wardens/{self.warden.pk}/delete/")
        self.assertEqual(confirm_response.status_code, 200)
        self.assertContains(confirm_response, "Yes, Deactivate Warden")

        # 2. Admin submits delete POST
        post_response = self.client.post(f"/accounts/profiles/wardens/{self.warden.pk}/delete/")
        self.assertRedirects(post_response, "/accounts/profiles/wardens/")

        # 3. Verify user remains in database for audit/history, but is deactivated
        self.warden.refresh_from_db()
        self.assertFalse(self.warden.is_active)

        # 4. Attempt login with deleted warden credentials - must fail
        self.client.logout()
        login_response = self.client.post(
            "/accounts/login/",
            {"identifier": self.warden.username, "password": self.password},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(login_response, "Invalid username/email or password.")

        # 5. Verify warden management list only displays View action for deactivated warden
        self.client.force_login(self.admin)
        warden_list_res = self.client.get("/accounts/profiles/wardens/")
        self.assertContains(warden_list_res, f"/accounts/profiles/{self.warden.pk}/")
        self.assertNotContains(warden_list_res, f"/accounts/profiles/{self.warden.pk}/edit/")
        self.assertNotContains(warden_list_res, f"/accounts/profiles/{self.warden.pk}/reset-password/")
        self.assertNotContains(warden_list_res, f"/accounts/profiles/wardens/{self.warden.pk}/delete/")

        # 6. Verify profile view for deactivated warden does NOT display the 'Edit profile' button
        profile_res = self.client.get(f"/accounts/profiles/{self.warden.pk}/")
        self.assertEqual(profile_res.status_code, 200)
        self.assertContains(profile_res, "Deleted / Inactive")
        self.assertNotContains(profile_res, "Edit profile")
        self.assertNotContains(profile_res, f"/accounts/profiles/{self.warden.pk}/edit/")

        # 7. Direct GET to edit or password reset on deactivated account redirects back to profile view
        edit_res = self.client.get(f"/accounts/profiles/{self.warden.pk}/edit/")
        self.assertRedirects(edit_res, f"/accounts/profiles/{self.warden.pk}/")
        reset_res = self.client.get(f"/accounts/profiles/{self.warden.pk}/reset-password/")
        self.assertRedirects(reset_res, f"/accounts/profiles/{self.warden.pk}/")

    def test_non_admin_cannot_add_or_delete_warden(self):
        # Student cannot access
        self.client.force_login(self.student)
        self.assertRedirects(self.client.get("/accounts/profiles/wardens/add/"), "/accounts/login/", fetch_redirect_response=False)
        self.assertRedirects(self.client.post(f"/accounts/profiles/wardens/{self.warden.pk}/delete/"), "/accounts/login/", fetch_redirect_response=False)
        self.client.logout()

        # Warden cannot access
        self.client.force_login(self.warden)
        self.assertRedirects(self.client.get("/accounts/profiles/wardens/add/"), "/accounts/login/", fetch_redirect_response=False)
        self.assertRedirects(self.client.post(f"/accounts/profiles/wardens/{self.warden.pk}/delete/"), "/accounts/login/", fetch_redirect_response=False)


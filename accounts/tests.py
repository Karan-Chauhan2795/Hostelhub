from django.contrib.auth import get_user_model
from django.test import TestCase


class LoginRedirectTests(TestCase):
    def test_demo_users_redirect_to_their_dashboards(self):
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="admin").exists())

        cases = [
            ("admin", "admin123", "/dashboard/admin/"),
            ("warden", "warden123", "/warden/"),
            ("student", "student123", "/student/"),
        ]

        for username, password, expected_path in cases:
            with self.subTest(username=username):
                response = self.client.post(
                    "/accounts/login/",
                    {"identifier": username, "password": password, "remember_me": "on"},
                    HTTP_HOST="localhost",
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], expected_path)

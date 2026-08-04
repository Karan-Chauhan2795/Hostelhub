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

    def test_student_signup_creates_student_and_redirects_to_login(self):
        response = self.client.post(
            "/accounts/create-student-account/",
            {
                "first_name": "Nisha",
                "last_name": "Patel",
                "username": "nisha_student",
                "email": "nisha@example.com",
                "phone_number": "+91 90000 11111",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/accounts/login/")

        User = get_user_model()
        user = User.objects.get(username="nisha_student")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password("StrongPass123!"))

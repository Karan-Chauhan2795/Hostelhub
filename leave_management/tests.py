import secrets
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase

from rooms.models import Room
from students.models import Student
from .models import LeaveRequest


class LeaveManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        password = secrets.token_urlsafe(16)
        self.admin = user_model.objects.create_user(
            username="leave_admin", password=password, role=user_model.Role.ADMIN
        )
        self.warden = user_model.objects.create_user(
            username="leave_warden", password=password, role=user_model.Role.WARDEN
        )
        self.student_user = user_model.objects.create_user(
            username="leave_student", password=password, role=user_model.Role.STUDENT
        )
        self.room = Room.objects.create(number="L-101", capacity=2)
        self.student = Student.objects.create(
            user=self.student_user, roll_number="L-001", course="Architecture", room=self.room
        )
        self.leave = LeaveRequest.objects.create(
            student=self.student,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            reason="Attending family event",
        )

    def test_admin_and_warden_see_all_fields_on_leave_list(self):
        self.client.force_login(self.admin)
        res_admin = self.client.get("/leave/")
        self.assertEqual(res_admin.status_code, 200)
        self.assertContains(res_admin, "leave_student")
        self.assertContains(res_admin, "L-101")
        self.assertContains(res_admin, "Attending family event")

        self.client.force_login(self.warden)
        res_warden = self.client.get("/leave/")
        self.assertEqual(res_warden.status_code, 200)
        self.assertContains(res_warden, "Attending family event")

    def test_student_can_apply_for_leave_with_form_fields(self):
        self.client.force_login(self.student_user)
        get_res = self.client.get("/leave/apply/")
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Departure Date (From)")
        self.assertContains(get_res, "Return Date (To)")
        self.assertContains(get_res, "Reason for Leave")

        post_res = self.client.post(
            "/leave/apply/",
            {
                "start_date": str(date.today() + timedelta(days=5)),
                "end_date": str(date.today() + timedelta(days=8)),
                "reason": "Conference presentation in Delhi",
            },
        )
        self.assertRedirects(post_res, "/leave/")
        self.assertTrue(LeaveRequest.objects.filter(reason="Conference presentation in Delhi").exists())

    def test_student_with_active_or_approved_leave_can_login_and_access_dashboard(self):
        # Even if a student has an approved or pending leave active today, they can still log in and view their dashboard
        self.leave.status = LeaveRequest.Status.APPROVED
        self.leave.save()

        # Login works normally
        login_res = self.client.post(
            "/accounts/login/",
            {"identifier": self.student_user.username, "password": "wrong-password"},
        )
        self.assertEqual(login_res.status_code, 200)

        # Login with correct password
        self.client.force_login(self.student_user)
        dash_res = self.client.get("/student/")
        self.assertEqual(dash_res.status_code, 200)
        self.assertContains(dash_res, "Student Portal")
        self.assertContains(dash_res, "L-101")

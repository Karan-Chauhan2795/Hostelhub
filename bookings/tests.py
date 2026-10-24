import secrets
from django.contrib.auth import get_user_model
from django.test import TestCase

from rooms.models import Room
from students.models import Student
from .models import Booking


class BookingWorkflowTests(TestCase):
    def setUp(self):
        password = secrets.token_urlsafe(16)
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="booking_admin", password=password, role=user_model.Role.ADMIN
        )
        self.warden = user_model.objects.create_user(
            username="booking_warden", password=password, role=user_model.Role.WARDEN
        )
        self.student_user = user_model.objects.create_user(
            username="booking_student", password=password, role=user_model.Role.STUDENT
        )
        self.room_current = Room.objects.create(number="B-204", capacity=2)
        self.room_target = Room.objects.create(number="A-101", capacity=2)
        self.student = Student.objects.create(
            user=self.student_user,
            roll_number="STU-BOOK-001",
            course="Computer Engineering",
            room=self.room_current,
        )

    def test_student_can_create_room_booking_with_message(self):
        self.client.force_login(self.student_user)
        response = self.client.post(
            "/bookings/create/",
            {
                "room": self.room_target.pk,
                "notes": "Requesting to shift to A-101 because of ground floor preference.",
            },
        )
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.filter(student=self.student).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.room, self.room_target)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(
            booking.request_message,
            "Requesting to shift to A-101 because of ground floor preference.",
        )

    def test_admin_and_warden_see_student_notes_and_can_cancel_with_reason(self):
        booking = Booking.objects.create(
            student=self.student,
            room=self.room_target,
            status=Booking.Status.PENDING,
            notes="Please shift me to A-101 to be near my study group.",
        )

        # Admin views bookings list
        self.client.force_login(self.admin)
        response = self.client.get("/bookings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please shift me to A-101 to be near my study group.")

        # Admin cancels with reason
        post_response = self.client.post(
            f"/bookings/{booking.pk}/status/",
            {
                "status": Booking.Status.CANCELLED,
                "rejection_reason": "Room A-101 is scheduled for plumbing maintenance next week.",
            },
        )
        self.assertEqual(post_response.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertEqual(
            booking.request_message,
            "Please shift me to A-101 to be near my study group.",
        )
        self.assertEqual(
            booking.rejection_reason,
            "Room A-101 is scheduled for plumbing maintenance next week.",
        )

        # Student checks booking list and sees both their note and the rejection reason
        self.client.force_login(self.student_user)
        student_response = self.client.get("/bookings/")
        self.assertContains(student_response, "Please shift me to A-101 to be near my study group.")
        self.assertContains(student_response, "Rejection Reason:")
        self.assertContains(student_response, "Room A-101 is scheduled for plumbing maintenance next week.")

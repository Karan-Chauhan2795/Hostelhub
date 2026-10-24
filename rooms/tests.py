import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from bookings.models import Booking
from students.models import Student
from .models import Room

User = get_user_model()


class RoomAPITests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="api_admin",
            email="admin@api.com",
            password="adminpassword123",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.warden = User.objects.create_user(
            username="api_warden",
            email="warden@api.com",
            password="wardenpassword123",
            role=User.Role.WARDEN,
        )
        self.student_user = User.objects.create_user(
            username="api_student",
            email="student@api.com",
            password="studentpassword123",
            role=User.Role.STUDENT,
        )
        self.room_1 = Room.objects.create(
            number="101-A",
            room_type=Room.RoomType.DOUBLE,
            capacity=2,
            monthly_fee=Decimal("4500.00"),
        )
        self.room_2 = Room.objects.create(
            number="102-B",
            room_type=Room.RoomType.SINGLE,
            capacity=1,
            monthly_fee=Decimal("7000.00"),
        )

    def test_unauthenticated_request_rejected(self):
        response = self.client.get("/rooms/api/")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_student_can_list_rooms_read_only(self):
        self.client.force_login(self.student_user)
        response = self.client.get("/rooms/api/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["rooms"]), 2)

    def test_student_cannot_create_room(self):
        self.client.force_login(self.student_user)
        payload = {
            "number": "201-C",
            "room_type": "DOUBLE",
            "capacity": 2,
            "monthly_fee": "5000.00",
        }
        response = self.client.post("/rooms/api/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Room.objects.filter(number="201-C").exists())

    def test_admin_and_warden_can_create_room(self):
        self.client.force_login(self.warden)
        payload = {
            "number": "201-W",
            "room_type": "TRIPLE",
            "capacity": 3,
            "monthly_fee": "3500.00",
        }
        response = self.client.post("/rooms/api/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["number"], "201-W")
        self.assertEqual(data["capacity"], 3)
        self.assertEqual(data["monthly_fee"], "3500.00")
        self.assertTrue(Room.objects.filter(number="201-W").exists())

    def test_create_validation_checks(self):
        self.client.force_login(self.admin)
        # Duplicate number
        payload = {
            "number": "101-A",
            "room_type": "SINGLE",
            "capacity": 1,
            "monthly_fee": "4000.00",
        }
        response = self.client.post("/rooms/api/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("number", response.json()["errors"])

        # Invalid room_type and negative fee
        payload = {
            "number": "301-X",
            "room_type": "PENTHOUSE",
            "capacity": -1,
            "monthly_fee": "-500",
        }
        response = self.client.post("/rooms/api/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("room_type", errors)
        self.assertIn("capacity", errors)
        self.assertIn("monthly_fee", errors)

    def test_malformed_json_and_unsupported_content_type(self):
        self.client.force_login(self.admin)
        # Unsupported content type
        response = self.client.post("/rooms/api/", data="number=301", content_type="text/plain")
        self.assertEqual(response.status_code, 415)

        # Malformed JSON
        response = self.client.post("/rooms/api/", data="{number: 301}", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_retrieve_room_detail(self):
        self.client.force_login(self.student_user)
        response = self.client.get(f"/rooms/api/{self.room_1.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["number"], "101-A")
        self.assertEqual(data["capacity"], 2)

        # Nonexistent room
        response = self.client.get("/rooms/api/99999/")
        self.assertEqual(response.status_code, 404)

    def test_update_room_put_and_patch(self):
        self.client.force_login(self.admin)
        # PATCH partial
        patch_payload = {"monthly_fee": "4800.00"}
        response = self.client.patch(f"/rooms/api/{self.room_1.pk}/", data=json.dumps(patch_payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.room_1.refresh_from_db()
        self.assertEqual(self.room_1.monthly_fee, Decimal("4800.00"))

        # PUT complete update
        put_payload = {
            "number": "101-Updated",
            "room_type": "DOUBLE",
            "capacity": 2,
            "monthly_fee": "4900.00",
        }
        response = self.client.put(f"/rooms/api/{self.room_1.pk}/", data=json.dumps(put_payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.room_1.refresh_from_db()
        self.assertEqual(self.room_1.number, "101-Updated")

    def test_delete_room_and_integrity_protection(self):
        self.client.force_login(self.admin)
        # Allocate student to room_1
        Student.objects.create(
            user=self.student_user,
            roll_number="STUDENT-001",
            course="Computer Science",
            room=self.room_1,
        )
        # Deleting room with resident must be rejected
        response = self.client.delete(f"/rooms/api/{self.room_1.pk}/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertTrue(Room.objects.filter(pk=self.room_1.pk).exists())

        # Deleting unallocated room_2 succeeds
        response = self.client.delete(f"/rooms/api/{self.room_2.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Room.objects.filter(pk=self.room_2.pk).exists())

import secrets

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notice


class NoticePaginationTests(TestCase):
    def test_second_page_contains_the_remaining_database_records(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="notice_admin", password=secrets.token_urlsafe(16), role=user_model.Role.ADMIN)
        Notice.objects.bulk_create([Notice(title=f"Notice {index}", body="Test notice", created_by=admin) for index in range(11)])
        self.client.force_login(admin)
        response = self.client.get("/notices/?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 1)

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

    def test_admin_can_edit_and_delete_notice(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="notice_mgr", password=secrets.token_urlsafe(16), role=user_model.Role.ADMIN)
        notice = Notice.objects.create(title="Original Title", body="Original Body", created_by=admin)

        self.client.force_login(admin)
        # Edit notice
        edit_response = self.client.post(
            f"/notices/{notice.pk}/edit/",
            {"title": "Updated Title", "body": "Updated Body", "audience": "WARDEN_ONLY"},
        )
        self.assertEqual(edit_response.status_code, 302)
        notice.refresh_from_db()
        self.assertEqual(notice.title, "[Warden Only] Updated Title")
        self.assertEqual(notice.body, "Updated Body")

        # Delete notice
        delete_response = self.client.post(f"/notices/{notice.pk}/delete/")
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Notice.objects.filter(pk=notice.pk).exists())

    def test_student_cannot_edit_or_delete_notice(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="admin_user", password=secrets.token_urlsafe(16), role=user_model.Role.ADMIN)
        student = user_model.objects.create_user(username="student_user", password=secrets.token_urlsafe(16), role=user_model.Role.STUDENT)
        notice = Notice.objects.create(title="General Notice", body="Info", created_by=admin)

        self.client.force_login(student)
        # Cannot access edit - redirected away with error message
        get_edit = self.client.get(f"/notices/{notice.pk}/edit/")
        self.assertEqual(get_edit.status_code, 302)
        self.assertIn("/accounts/login/", get_edit.url)

        # Cannot access delete - redirected away without deleting
        post_del = self.client.post(f"/notices/{notice.pk}/delete/")
        self.assertEqual(post_del.status_code, 302)
        self.assertIn("/accounts/login/", post_del.url)
        self.assertTrue(Notice.objects.filter(pk=notice.pk).exists())

    def test_warden_can_only_edit_and_delete_own_notices(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="admin_author", password=secrets.token_urlsafe(16), role=user_model.Role.ADMIN)
        warden = user_model.objects.create_user(username="warden_user", password=secrets.token_urlsafe(16), role=user_model.Role.WARDEN)

        admin_notice = Notice.objects.create(title="Admin Notice", body="Important", created_by=admin)
        warden_notice = Notice.objects.create(title="Warden Notice", body="Inspection", created_by=warden)

        self.client.force_login(warden)

        # Warden CANNOT edit Admin notice -> 404
        edit_admin_resp = self.client.post(
            f"/notices/{admin_notice.pk}/edit/",
            {"title": "Hacked Title", "body": "Modified", "audience": "ALL"},
        )
        self.assertEqual(edit_admin_resp.status_code, 404)
        admin_notice.refresh_from_db()
        self.assertEqual(admin_notice.title, "Admin Notice")

        # Warden CANNOT delete Admin notice -> 404
        delete_admin_resp = self.client.post(f"/notices/{admin_notice.pk}/delete/")
        self.assertEqual(delete_admin_resp.status_code, 404)
        self.assertTrue(Notice.objects.filter(pk=admin_notice.pk).exists())

        # Warden CAN edit own notice
        edit_warden_resp = self.client.post(
            f"/notices/{warden_notice.pk}/edit/",
            {"title": "Updated Warden Notice", "body": "Inspection done", "audience": "ALL"},
        )
        self.assertEqual(edit_warden_resp.status_code, 302)
        warden_notice.refresh_from_db()
        self.assertEqual(warden_notice.title, "Updated Warden Notice")

        # Warden CAN delete own notice
        delete_warden_resp = self.client.post(f"/notices/{warden_notice.pk}/delete/")
        self.assertFalse(Notice.objects.filter(pk=warden_notice.pk).exists())

    def test_warden_form_does_not_have_audience_choice_and_publishes_for_all(self):
        user_model = get_user_model()
        warden = user_model.objects.create_user(username="warden_pub", password=secrets.token_urlsafe(16), role=user_model.Role.WARDEN)
        self.client.force_login(warden)

        # GET form does not contain audience select
        get_resp = self.client.get("/notices/create/")
        self.assertEqual(get_resp.status_code, 200)
        self.assertNotContains(get_resp, "Audience")

        # POST publishes notice without [Warden Only] prefix so everyone sees it
        post_resp = self.client.post("/notices/create/", {"title": "Hostel Inspection", "body": "Tomorrow 10 AM"})
        self.assertEqual(post_resp.status_code, 302)
        notice = Notice.objects.get(title="Hostel Inspection")
        self.assertEqual(notice.created_by, warden)
        self.assertFalse(notice.title.startswith("[Warden Only]"))


    def test_student_sees_notice_author_attribution(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="chief_admin", password=secrets.token_urlsafe(16), role=user_model.Role.ADMIN)
        warden = user_model.objects.create_user(username="hostel_warden", password=secrets.token_urlsafe(16), role=user_model.Role.WARDEN)
        student = user_model.objects.create_user(username="student_viewer", password=secrets.token_urlsafe(16), role=user_model.Role.STUDENT)

        notice_admin = Notice.objects.create(title="Fee Payment Deadline", body="Please pay by Friday", created_by=admin)
        notice_warden = Notice.objects.create(title="Cleanliness Drive", body="Join Sunday cleaning", created_by=warden)

        self.client.force_login(student)

        # List view contains author designations
        list_resp = self.client.get("/notices/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, "Admin")
        self.assertContains(list_resp, "Warden")

        # Detail view contains author designations
        detail_admin_resp = self.client.get(f"/notices/{notice_admin.pk}/")
        self.assertEqual(detail_admin_resp.status_code, 200)
        self.assertContains(detail_admin_resp, "Admin &middot;")

        detail_warden_resp = self.client.get(f"/notices/{notice_warden.pk}/")
        self.assertEqual(detail_warden_resp.status_code, 200)
        self.assertContains(detail_warden_resp, "Warden &middot;")


    def test_notice_title_named_warden_preserves_full_title(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(username="chief_adm2", password=secrets.token_urlsafe(16), role=user_model.Role.ADMIN)
        notice = Notice.objects.create(title="[Warden Only] warden", body="warden staff", created_by=admin)

        self.assertEqual(notice.clean_display_title, "warden")
        self.assertTrue(notice.is_warden_only)

        self.client.force_login(admin)
        list_resp = self.client.get("/notices/")
        self.assertContains(list_resp, "warden")
        self.assertNotContains(list_resp, ">arden<")

        detail_resp = self.client.get(f"/notices/{notice.pk}/")
        self.assertContains(detail_resp, "warden")
        self.assertNotContains(detail_resp, ">arden<")






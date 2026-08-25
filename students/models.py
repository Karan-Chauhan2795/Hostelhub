from django.conf import settings
from django.db import models


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    roll_number = models.CharField(max_length=30, unique=True)
    course = models.CharField(max_length=120)
    room = models.ForeignKey("rooms.Room", on_delete=models.SET_NULL, null=True, blank=True, related_name="residents")
    emergency_contact = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("roll_number",)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

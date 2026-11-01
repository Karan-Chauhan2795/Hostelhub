from django.db import models
from django.utils import timezone
from accounts.models import User


class HostelEvent(models.Model):
    class EventType(models.TextChoices):
        DINNER = "DINNER", "Community Dinner"
        MEETING = "MEETING", "Hostel Meeting"
        MAINTENANCE = "MAINTENANCE", "Maintenance / Inspection"
        SPORTS = "SPORTS", "Sports / Cultural"
        CELEBRATION = "CELEBRATION", "Festival / Celebration"
        OTHER = "OTHER", "General Event"

    class Audience(models.TextChoices):
        ALL = "ALL", "For All (Students & Wardens)"
        WARDEN_ONLY = "WARDEN_ONLY", "Warden Only"

    title = models.CharField(max_length=150)
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER,
    )
    audience = models.CharField(
        max_length=20,
        choices=Audience.choices,
        default=Audience.ALL,
        help_text="Target audience for this event",
    )
    event_date = models.DateField(default=timezone.localdate, db_index=True)
    event_time = models.TimeField(default="19:30:00")
    end_time = models.TimeField(null=True, blank=True, help_text="Event conclusion time")
    location = models.CharField(max_length=120, default="Dining Hall / Common Area")
    description = models.TextField(blank=True, default="")
    is_recurring_daily = models.BooleanField(
        default=False,
        help_text="If set, this event is standard across every day unless specifically overridden.",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date", "event_time"]
        verbose_name = "Hostel Event"
        verbose_name_plural = "Hostel Events"

    def __str__(self):
        return f"{self.title} ({self.event_date} {self.event_time})"

    @property
    def formatted_time_range(self):
        start = self.event_time.strftime("%I:%M %p").lstrip("0")
        if self.end_time:
            end = self.end_time.strftime("%I:%M %p").lstrip("0")
            return f"{start} – {end}"
        return start


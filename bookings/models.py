from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="bookings")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-requested_at",)

    def __str__(self):
        return f"Booking #{self.pk}"

    @property
    def request_message(self):
        """Returns the message/notes submitted by the student when requesting the room."""
        if not self.notes:
            return ""
        if "\n[Rejection Reason]:" in self.notes:
            return self.notes.split("\n[Rejection Reason]:", 1)[0].replace("[Student Note]:", "").strip()
        if self.notes.startswith("[Rejection Reason]:"):
            return ""
        return self.notes.replace("[Student Note]:", "").strip()

    @property
    def rejection_reason(self):
        """Returns the rejection/cancellation reason given by admin or warden, if any."""
        if not self.notes:
            return ""
        if "\n[Rejection Reason]:" in self.notes:
            return self.notes.split("\n[Rejection Reason]:", 1)[1].strip()
        if self.notes.startswith("[Rejection Reason]:"):
            return self.notes.replace("[Rejection Reason]:", "", 1).strip()
        return ""

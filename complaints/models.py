from django.db import models


class Complaint(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="complaints")
    subject = models.CharField(max_length=160)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.subject

    @property
    def student_sequence_number(self):
        """Sequential number of this complaint for its specific student (1-indexed based on creation date)."""
        if hasattr(self, "student_seq") and self.student_seq:
            return self.student_seq
        if self.student_id and self.created_at:
            return Complaint.objects.filter(student_id=self.student_id, created_at__lte=self.created_at).count()
        return self.id or 1

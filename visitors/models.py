from django.db import models


class Visitor(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="visitors")
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    purpose = models.CharField(max_length=200)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-check_in",)

    def __str__(self):
        return self.name

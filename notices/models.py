from django.db import models


class Notice(models.Model):
    title = models.CharField(max_length=180)
    body = models.TextField()
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="notices")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

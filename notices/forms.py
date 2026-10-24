from django import forms

from .models import Notice


class NoticeForm(forms.ModelForm):
    AUDIENCE_CHOICES = [
        ("ALL", "All Residents & Wardens (General)"),
        ("WARDEN_ONLY", "Warden Only (Staff)"),
    ]
    audience = forms.ChoiceField(
        choices=AUDIENCE_CHOICES,
        initial="ALL",
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Audience",
        help_text="Choose who should see this notice.",
    )

    class Meta:
        model = Notice
        fields = ["title", "audience", "body"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Wardens always publish for everyone (Admins and Students); only Admins can select Warden Only
        if self.user and self.user.role == "WARDEN":
            self.fields.pop("audience", None)

        if self.instance and self.instance.pk:
            if self.instance.title.startswith("[Warden Only] "):
                if "audience" in self.fields:
                    self.initial["audience"] = "WARDEN_ONLY"
                self.initial["title"] = self.instance.title.replace("[Warden Only] ", "", 1)

    def save(self, commit=True):
        notice = super().save(commit=False)
        audience = self.cleaned_data.get("audience", "ALL")
        clean_title = self.cleaned_data.get("title", "").strip()
        if clean_title.startswith("[Warden Only] "):
            clean_title = clean_title.replace("[Warden Only] ", "", 1)

        if audience == "WARDEN_ONLY":
            notice.title = f"[Warden Only] {clean_title}"
        else:
            notice.title = clean_title

        if commit:
            notice.save()
        return notice


from django import forms
from .models import HostelEvent


class HostelEventForm(forms.ModelForm):
    class Meta:
        model = HostelEvent
        fields = [
            "title",
            "event_type",
            "audience",
            "event_date",
            "event_time",
            "end_time",
            "location",
            "description",
            "is_recurring_daily",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g., Community Dinner, Hostel Meeting, Sports Night"}),
            "event_type": forms.Select(),
            "audience": forms.Select(),
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "event_time": forms.TimeInput(attrs={"type": "time", "step": "1"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "step": "1"}),
            "location": forms.TextInput(attrs={"placeholder": "e.g., Dining Hall, Ground Floor Common Area"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Details, agenda, preparations or timings..."}),
            "is_recurring_daily": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "is_recurring_daily":
                field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("event_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "End time must be after the start time.")

        return cleaned_data


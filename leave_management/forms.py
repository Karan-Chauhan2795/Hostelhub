from django import forms

from .models import LeaveRequest


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["start_date", "end_date", "reason"]

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("start_date") and cleaned_data.get("end_date") and cleaned_data["end_date"] < cleaned_data["start_date"]:
            self.add_error("end_date", "The return date cannot be before the departure date.")
        return cleaned_data


class LeaveStatusForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["status"]

from django import forms

from .models import LeaveRequest


class LeaveRequestForm(forms.ModelForm):
    start_date = forms.DateField(
        label="Departure Date (From)",
        help_text="Select the date you will leave the hostel premises.",
        widget=forms.DateInput(attrs={"type": "date", "class": "search-box", "style": "width: 100%; min-height: 40px;"}),
    )
    end_date = forms.DateField(
        label="Return Date (To)",
        help_text="Select the date you are scheduled to return to the hostel.",
        widget=forms.DateInput(attrs={"type": "date", "class": "search-box", "style": "width: 100%; min-height: 40px;"}),
    )
    reason = forms.CharField(
        label="Reason for Leave",
        help_text="Provide a clear explanation for the hostel administration (e.g. Family Function, Medical Emergency, Academic Internship).",
        widget=forms.Textarea(
            attrs={
                "class": "search-box",
                "rows": 4,
                "style": "width: 100%; min-height: 100px; padding: 10px 12px; font-family: inherit;",
                "placeholder": "Explain the purpose of your leave request and destination if applicable...",
            }
        ),
    )

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

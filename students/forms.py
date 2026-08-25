from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["user", "roll_number", "course", "room", "emergency_contact"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = self.fields["user"].queryset.filter(role="STUDENT")

from django import forms

from students.models import Student
from .models import Visitor


class StudentModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        name = obj.user.get_full_name() or obj.user.username
        room_info = f"Room {obj.room.number}" if obj.room else "Unassigned Room"
        return f"{name} ({obj.roll_number}) — {room_info}"


class VisitorForm(forms.ModelForm):
    student = StudentModelChoiceField(
        queryset=Student.objects.select_related("user", "room").order_by("user__first_name", "user__last_name", "roll_number"),
        empty_label="Select host resident...",
        label="Host Resident (Student)",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Visitor
        fields = ["student", "name", "relation", "phone", "purpose"]
        labels = {
            "student": "Host Resident (Student)",
            "name": "Visitor Full Name",
            "relation": "Relation with Student",
            "phone": "Contact Phone Number",
            "purpose": "Purpose of Visit",
        }
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "e.g., Rajesh Sharma",
                "autocomplete": "name"
            }),
            "relation": forms.TextInput(attrs={
                "placeholder": "e.g., Father, Mother, Brother, Sister, Guardian, Friend, Relative",
                "autocomplete": "off"
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "e.g., +91 98765 43210",
                "autocomplete": "tel"
            }),
            "purpose": forms.TextInput(attrs={
                "placeholder": "e.g., Meeting with family, dropping off winter clothes",
                "autocomplete": "off"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_descriptions = {
            "student": "Choose the registered resident whom this visitor is visiting (displays student name, roll number, and room assignment).",
            "name": "Full legal name of the visitor as per official government photo ID card.",
            "relation": "Specify the relationship to the resident (e.g., Father, Mother, Guardian, Sibling, Friend, Courier).",
            "phone": "Active 10-digit mobile number of the visitor for safety, security verification, and contact records.",
            "purpose": "Reason for entering the hostel premises (e.g., Routine family visit, Delivering medicines/essentials, Luggage handover).",
        }
        for field_name, desc in field_descriptions.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = desc

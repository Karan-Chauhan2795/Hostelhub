from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["room", "notes"]
        labels = {
            "room": "Target Room to Shift / Book",
            "notes": "Request Message / Reason for Shift",
        }
        help_texts = {
            "room": "Select the room you wish to allocate or shift into.",
            "notes": "Please specify why you want to move or book this room (e.g. preferred roommate, floor preference, ventilation, or study needs).",
        }
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Enter your message or reason for shifting to this room...",
                }
            )
        }

    def clean_room(self):
        room = self.cleaned_data["room"]
        if room.occupied_count >= room.capacity:
            raise forms.ValidationError("This room is already at capacity.")
        return room


class BookingStatusForm(forms.ModelForm):
    rejection_reason = forms.CharField(
        required=False,
        label="Rejection / Cancellation Reason",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Reason for rejection (e.g. room under maintenance, capacity reached)",
            }
        ),
    )

    class Meta:
        model = Booking
        fields = ["status"]

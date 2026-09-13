from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["room", "notes"]

    def clean_room(self):
        room = self.cleaned_data["room"]
        if room.occupied_count >= room.capacity:
            raise forms.ValidationError("This room is already at capacity.")
        return room


class BookingStatusForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["status"]

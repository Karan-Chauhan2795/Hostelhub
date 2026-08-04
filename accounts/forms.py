from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class LoginForm(forms.Form):
    identifier = forms.CharField(
        label="Username or Email",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "placeholder": "Enter username or email",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Enter password",
            }
        ),
    )
    remember_me = forms.BooleanField(required=False, label="Remember me")


class StudentSignupForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "First name"}),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Last name"}),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Choose a username"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "student@example.com"}),
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+91 98765 43210"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Create a password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Confirm password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user

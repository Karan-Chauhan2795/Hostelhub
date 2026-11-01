from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, UserCreationForm

from rooms.models import Room
from students.models import Student

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

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"].strip().lower()
        user.phone_number = self.cleaned_data["phone_number"].strip()
        user.role = User.Role.STUDENT
        user.is_active = True
        if commit:
            user.save()
        return user


class WardenCreationForm(UserCreationForm):
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
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "warden@example.com"}),
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+91 98765 43210"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"].strip().lower()
        user.phone_number = self.cleaned_data["phone_number"].strip()
        user.role = User.Role.WARDEN
        user.is_active = True
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=False,
        label="Username",
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Account username"}),
        help_text="Login identifier for this account.",
    )
    first_name = forms.CharField(
        max_length=150,
        label="First Name",
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "First name"}),
        help_text="Given name.",
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Last Name",
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Last name"}),
        help_text="Surname / Family name.",
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "email@example.com"}),
        help_text="Official email address used for notifications and account recovery.",
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Contact / Phone Number",
        widget=forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+91 98765 43210"}),
        help_text="Primary contact number of the user.",
    )

    # Student-specific fields (populated and displayed when editing a student)
    roll_number = forms.CharField(
        max_length=30,
        required=False,
        label="Roll Number / Student ID",
        widget=forms.TextInput(attrs={"placeholder": "e.g. HH2026001"}),
        help_text="Official student registration/enrollment identifier.",
    )
    course = forms.CharField(
        max_length=120,
        required=False,
        label="Academic Course / Degree",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Computer Science & Engineering"}),
        help_text="Academic program enrolled in.",
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.all().order_by("number"),
        required=False,
        empty_label="Unassigned / No Room Allocated",
        label="Room Allocation",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Designated hostel room for this resident.",
    )
    emergency_contact = forms.CharField(
        max_length=150,
        required=False,
        label="Emergency Contact / Guardian",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Rajesh Sharma (+91 98765 43210)"}),
        help_text="Name and phone number of parent or emergency contact person.",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance
        if user and user.pk:
            self.fields["username"].initial = user.username
            if user.role == User.Role.STUDENT:
                student = getattr(user, "student_profile", None)
                if student:
                    self.fields["roll_number"].initial = student.roll_number
                    self.fields["course"].initial = student.course
                    self.fields["room"].initial = student.room
                    self.fields["emergency_contact"].initial = student.emergency_contact
                self.fields["roll_number"].required = True
                self.fields["course"].required = True
            else:
                # Hide student fields for Wardens and Administrators
                del self.fields["roll_number"]
                del self.fields["course"]
                del self.fields["room"]
                del self.fields["emergency_contact"]

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username and self.instance and self.instance.pk:
            return self.instance.username
        user_pk = self.instance.pk if self.instance else None
        if username and User.objects.filter(username__iexact=username).exclude(pk=user_pk).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        user_pk = self.instance.pk if self.instance else None
        if email and User.objects.filter(email__iexact=email).exclude(pk=user_pk).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean_roll_number(self):
        if "roll_number" in self.fields:
            roll_number = self.cleaned_data.get("roll_number", "").strip()
            student = getattr(self.instance, "student_profile", None)
            student_pk = student.pk if student else None
            if roll_number and Student.objects.filter(roll_number__iexact=roll_number).exclude(pk=student_pk).exists():
                raise forms.ValidationError("Another student with this roll number already exists.")
            return roll_number
        return None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["username"]
        if commit:
            user.save()
            if user.role == User.Role.STUDENT and hasattr(user, "student_profile"):
                student = user.student_profile
                student.roll_number = self.cleaned_data.get("roll_number", student.roll_number)
                student.course = self.cleaned_data.get("course", student.course)
                student.room = self.cleaned_data.get("room")
                student.emergency_contact = self.cleaned_data.get("emergency_contact", student.emergency_contact)
                student.save()
        return user


class AdminPasswordResetForm(SetPasswordForm):
    """Uses Django's password validators for an administrator-assisted reset."""


class HostelHubPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "Enter your registered email address",
                "id": "id_email",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email = email.strip()
            if not User._default_manager.filter(email__iexact=email).exists():
                raise forms.ValidationError("No account found with this email address. Please check and try again.")
            if not User._default_manager.filter(email__iexact=email, is_active=True).exists():
                raise forms.ValidationError("This account has been deactivated. Please contact the hostel office.")
        return email

    def get_users(self, email):
        """Allow active users with matching email to reset or create their password, even if registered via Google OAuth."""
        active_users = User._default_manager.filter(email__iexact=email, is_active=True)
        return (u for u in active_users)


class HostelHubSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Enter new password"}
        )
        self.fields["new_password2"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Confirm new password"}
        )

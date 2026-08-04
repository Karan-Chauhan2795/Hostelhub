from django import forms


class LoginForm(forms.Form):
    identifier = forms.CharField(
        label="Username or Email",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Enter username or email"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
    )
    remember_me = forms.BooleanField(required=False, label="Remember me")

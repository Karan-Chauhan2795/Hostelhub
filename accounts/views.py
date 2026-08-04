from django.views.generic import TemplateView


class LoginView(TemplateView):
    template_name = "accounts/login.html"


class LogoutView(TemplateView):
    template_name = "accounts/logout.html"


class ForgotPasswordView(TemplateView):
    template_name = "accounts/forgot_password.html"


class ResetPasswordView(TemplateView):
    template_name = "accounts/reset_password.html"


class ProfileView(TemplateView):
    template_name = "accounts/profile.html"


class EditProfileView(TemplateView):
    template_name = "accounts/edit_profile.html"

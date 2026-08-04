from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, View

from .forms import LoginForm
from .mixins import RoleRequiredMixin

User = get_user_model()


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._redirect_url_for_role(request.user))
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            password = form.cleaned_data["password"]
            user = None

            if "@" in identifier:
                user = User.objects.filter(email__iexact=identifier).first()
            else:
                user = User.objects.filter(username__iexact=identifier).first()

            authenticated_user = None
            if user is not None:
                authenticated_user = authenticate(
                    request,
                    username=user.username,
                    password=password,
                )
            else:
                authenticated_user = authenticate(
                    request,
                    username=identifier,
                    password=password,
                )

            if authenticated_user is not None:
                login(request, authenticated_user)
                if form.cleaned_data["remember_me"]:
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                messages.success(
                    request,
                    f"Welcome back, {authenticated_user.get_full_name() or authenticated_user.username}!",
                )
                return redirect(self._redirect_url_for_role(authenticated_user))

            messages.error(request, "Invalid username/email or password.")

        return render(request, self.template_name, {"form": form})

    def _redirect_url_for_role(self, user):
        if user.role == User.Role.ADMIN:
            return "dashboard:admin_dashboard"
        if user.role == User.Role.WARDEN:
            return "dashboard:warden_dashboard"
        return "dashboard:student_dashboard"


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("accounts:login")


class ForgotPasswordView(TemplateView):
    template_name = "accounts/forgot_password.html"


class ProfileView(RoleRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
    allowed_roles = (User.Role.ADMIN, User.Role.WARDEN, User.Role.STUDENT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_data"] = {
            "full_name": self.request.user.get_full_name() or self.request.user.username,
            "email": self.request.user.email or "student@hostelhub.edu",
            "role": self.request.user.get_role_display(),
            "contact": "+91 98765 43210",
            "room": "B-204",
            "phone": "+91 99999 88888",
            "guardian": "Mr. S. Sharma",
        }
        return context

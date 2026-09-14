from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.views.generic import TemplateView, UpdateView, View

from .forms import LoginForm, ProfileForm, StudentSignupForm
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
                request.session.set_expiry(settings.SESSION_COOKIE_AGE if form.cleaned_data["remember_me"] else 0)
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
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        return redirect("dashboard:home" if request.user.is_authenticated else "dashboard:landing")

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, "You have been logged out.")
        return redirect("dashboard:landing")


class StudentSignupView(View):
    template_name = "accounts/signup.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return render(request, self.template_name, {"form": StudentSignupForm()})

    def post(self, request, *args, **kwargs):
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            from students.models import Student
            Student.objects.get_or_create(
                user=user,
                defaults={"roll_number": f"STU-{user.pk:06d}", "course": "Not provided"},
            )
            messages.success(request, "Student account created successfully. Please login.")
            return redirect("accounts:login")
        return render(request, self.template_name, {"form": form})


class ForgotPasswordView(PasswordResetView):
    template_name = "accounts/forgot_password.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class ForgotPasswordDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class ResetPasswordCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class ProfileView(RoleRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
    allowed_roles = (User.Role.ADMIN, User.Role.WARDEN, User.Role.STUDENT)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = getattr(self.request.user, "student_profile", None) if self.request.user.role == User.Role.STUDENT else None
        context["profile_data"] = {
            "full_name": self.request.user.get_full_name() or self.request.user.username,
            "email": self.request.user.email or "Not provided",
            "role": self.request.user.get_role_display(),
            "contact": self.request.user.phone_number or "Not provided",
            "room": student.room.number if student and student.room else "Not assigned",
            "phone": self.request.user.phone_number or "Not provided",
            "guardian": student.emergency_contact if student and student.emergency_contact else "Not provided",
        }
        return context


class ProfileUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "accounts/edit_profile.html"
    form_class = ProfileForm
    success_url = reverse_lazy("accounts:profile")
    allowed_roles = (User.Role.ADMIN, User.Role.WARDEN, User.Role.STUDENT)

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)

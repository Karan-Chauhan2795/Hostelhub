import secrets
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.views.generic import FormView, TemplateView, UpdateView, View

from .forms import AdminPasswordResetForm, LoginForm, ProfileForm, StudentSignupForm
from .mixins import RoleRequiredMixin

User = get_user_model()

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


def exchange_google_code(code):
    data = urlencode(
        {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )
    request = Request(GOOGLE_TOKEN_ENDPOINT, data=data.encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read())["id_token"]


def verify_google_token(token):
    import urllib3

    from google.auth.transport import urllib3 as google_urllib3
    from google.oauth2 import id_token

    return id_token.verify_oauth2_token(
        token,
        # google-auth's urllib3 transport needs an explicit connection pool.
        google_urllib3.Request(urllib3.PoolManager()),
        settings.GOOGLE_OAUTH_CLIENT_ID,
    )


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


class GoogleLoginView(View):
    """Start the Google OIDC authorization-code flow with CSRF/replay guards."""

    def get(self, request, *args, **kwargs):
        if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET or not settings.GOOGLE_OAUTH_REDIRECT_URI:
            messages.error(request, "Google sign-in is not configured yet.")
            return redirect("accounts:login")
        if request.GET.get("signup") == "1":
            request.session["google_oauth_signup"] = True
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        request.session["google_oauth_state"] = state
        request.session["google_oauth_nonce"] = nonce
        query = urlencode({
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
        })
        return redirect(f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{query}")


class GoogleSignupView(GoogleLoginView):
    """Begin Google sign-up; only the callback may create a Student account."""

    def get(self, request, *args, **kwargs):
        request.session["google_oauth_signup"] = True
        return super().get(request, *args, **kwargs)


def google_username(email):
    base = slugify(email.split("@", 1)[0])[:140] or "student"
    username = base
    suffix = 1
    while User.objects.filter(username__iexact=username).exists():
        suffix += 1
        username = f"{base[:150 - len(str(suffix)) - 1]}-{suffix}"
    return username


class GoogleCallbackView(View):
    def get(self, request, *args, **kwargs):
        state = request.session.pop("google_oauth_state", "")
        nonce = request.session.pop("google_oauth_nonce", "")
        signup_requested = request.session.pop("google_oauth_signup", False)
        if not state or not secrets.compare_digest(state, request.GET.get("state", "")):
            messages.error(request, "Google sign-in could not be verified. Please try again.")
            return redirect("accounts:login")
        if request.GET.get("error") or not request.GET.get("code"):
            messages.error(request, "Google sign-in was cancelled or failed.")
            return redirect("accounts:login")
        try:
            claims = verify_google_token(exchange_google_code(request.GET["code"]))
        except (HTTPError, ImportError, KeyError, URLError, ValueError):
            messages.error(request, "Google sign-in could not be completed. Please try again.")
            return redirect("accounts:login")
        if claims.get("nonce") != nonce or not claims.get("email_verified") or not claims.get("email"):
            messages.error(request, "Google did not provide a verified email address.")
            return redirect("accounts:login")
        users = User.objects.filter(email__iexact=claims["email"], is_active=True)
        if users.count() == 0 and signup_requested:
            from students.models import Student

            name_parts = (claims.get("name") or "").split(maxsplit=1)
            user = User.objects.create_user(
                username=google_username(claims["email"]),
                email=claims["email"],
                first_name=claims.get("given_name") or (name_parts[0] if name_parts else ""),
                last_name=claims.get("family_name") or (name_parts[1] if len(name_parts) > 1 else ""),
                role=User.Role.STUDENT,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            Student.objects.create(user=user, roll_number=f"STU-{user.pk:06d}", course="Not provided")
            login(request, user)
            messages.success(request, "Your Student account has been created with Google.")
            return redirect("dashboard:student_dashboard")
        if users.count() != 1:
            messages.error(request, "No single HostelHub account matches this Google email. Contact an administrator.")
            return redirect("accounts:login")
        user = users.get()
        login(request, user)
        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
        return redirect(LoginView()._redirect_url_for_role(user))


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
    allowed_roles = (User.Role.ADMIN,)

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class ManagedProfileView(ProfileView):
    allowed_roles = (User.Role.ADMIN,)

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        profile_user = get_object_or_404(User, pk=self.kwargs["pk"], role__in=(User.Role.STUDENT, User.Role.WARDEN))
        student = getattr(profile_user, "student_profile", None)
        context["profile_data"] = {
            "full_name": profile_user.get_full_name() or profile_user.username,
            "username": profile_user.username,
            "email": profile_user.email or "Not provided",
            "role": profile_user.get_role_display(),
            "contact": profile_user.phone_number or "Not provided",
            "room": student.room.number if student and student.room else "Not assigned",
            "phone": profile_user.phone_number or "Not provided",
            "guardian": student.emergency_contact if student and student.emergency_contact else "Not provided",
        }
        context["managed_profile"] = True
        return context


class ManagedProfileUpdateView(RoleRequiredMixin, UpdateView):
    template_name = "accounts/edit_profile.html"
    form_class = ProfileForm
    allowed_roles = (User.Role.ADMIN,)

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs["pk"], role__in=(User.Role.STUDENT, User.Role.WARDEN))

    def get_success_url(self):
        return reverse_lazy("accounts:managed_profile", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class ManagedPasswordResetView(RoleRequiredMixin, FormView):
    """Secure, administrator-assisted recovery for existing residents/staff."""

    template_name = "accounts/admin_password_reset.html"
    form_class = AdminPasswordResetForm
    allowed_roles = (User.Role.ADMIN,)

    def get_target_user(self):
        return get_object_or_404(
            User,
            pk=self.kwargs["pk"],
            role__in=(User.Role.STUDENT, User.Role.WARDEN),
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.get_target_user()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Password reset. Give the new password to the account holder securely.")
        return redirect("accounts:managed_profile", pk=self.get_target_user().pk)


class WardenManagementView(RoleRequiredMixin, TemplateView):
    template_name = "accounts/warden_management.html"
    allowed_roles = (User.Role.ADMIN,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["wardens"] = User.objects.filter(role=User.Role.WARDEN).order_by("username")
        return context

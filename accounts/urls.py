from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("create-student-account/", views.StudentSignupView.as_view(), name="signup"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("forgot-password/done/", views.ForgotPasswordDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.ResetPasswordConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/complete/", views.ResetPasswordCompleteView.as_view(), name="password_reset_complete"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("profiles/wardens/", views.WardenManagementView.as_view(), name="warden_management"),
    path("profiles/<int:pk>/", views.ManagedProfileView.as_view(), name="managed_profile"),
    path("profiles/<int:pk>/edit/", views.ManagedProfileUpdateView.as_view(), name="managed_profile_edit"),
]

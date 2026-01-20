from django.urls import path
from userauths import views

app_name = "userauths"

urlpatterns = [
    path("sign-up/", views.RegisterView, name="sign-up"),
    path("sign-in/", views.LoginView, name="sign-in"),
    path("sign-out/", views.LogoutView, name="sign-out"),
    path("my-profile/", views.my_profile, name="my-profile"),
    path("profile/<username>/", views.friend_profile, name="profile"),
    path("verify-email/<uidb64>/<token>", views.VerifyEmail, name="verify-email"),
    path("settings/", views.settings_view, name="settings"),
    path("edit-profile/", views.edit_profile, name="edit-profile"),
]

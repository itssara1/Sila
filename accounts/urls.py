from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "accounts"
urlpatterns = [
    path("login/", views.SilaLoginView.as_view(), name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", views.profile_update, name="profile"),
]

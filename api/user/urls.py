"""URL configurations for the user app."""
from django.urls import include, path
from rest_framework_simplejwt.views import TokenBlacklistView

app_name = "user"

urlpatterns = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
    path("", include("djoser.social.urls")),
    path("jwt/blacklist/", TokenBlacklistView.as_view(), name="jwt-blacklist"),
]

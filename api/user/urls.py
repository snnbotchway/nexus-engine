"""URL configurations for the user app."""
from django.urls import include, path

app_name = "user"

urlpatterns = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
]

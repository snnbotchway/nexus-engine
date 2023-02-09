"""URL configurations for the user app."""
from django.urls import include
from django.urls import path

app_name = "user"

urlpatterns = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
]

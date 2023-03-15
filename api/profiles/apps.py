"""Configuration for the profile app of this Django project."""
from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """The configuration class for the profile app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"

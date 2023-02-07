"""Configuration for the User app of this Django project."""
from django.apps import AppConfig


class UserConfig(AppConfig):
    """Application configuration for the user app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "user"

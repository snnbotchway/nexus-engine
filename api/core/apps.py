"""Configuration for the Core app in the Django project."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """The configuration class for the Core app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

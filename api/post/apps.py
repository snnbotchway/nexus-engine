"""Post app configuration."""
from django.apps import AppConfig


class PostConfig(AppConfig):
    """Post app class config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "post"

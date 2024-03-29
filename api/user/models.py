"""User app models."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model for this project."""

    email = models.EmailField(_("email address"), blank=False, null=False, unique=True)
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False, null=False
    )

    REQUIRED_FIELDS = [
        "email",
        "first_name",
        "last_name",
    ]

    def __str__(self):
        """Return username."""
        return self.username

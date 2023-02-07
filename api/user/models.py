"""User app models."""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model for this project."""

    name = models.CharField(
        _("name"),
        max_length=150,
        blank=False,
        null=False,
    )
    email = models.EmailField(_("email address"), blank=False, null=False, unique=True)
    first_name = None
    last_name = None

    REQUIRED_FIELDS = [
        "email",
        "name",
    ]

    def __str__(self):
        """Return username."""
        return self.username

    def save(self, *args, **kwargs):
        """Validate email and name, then save."""
        if not self.email:
            raise ValidationError({"email": "This field is required."})
        if not self.name:
            raise ValidationError({"name": "This field is required."})
        super().save(*args, **kwargs)

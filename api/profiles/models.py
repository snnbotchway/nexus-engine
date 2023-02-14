"""Profile app models."""
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


def profile_image_file_path(instance, filename):
    """Generate file path for new profile image."""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    return os.path.join("uploads/profile/", filename)


def validate_age(value):
    """Ensure user is at least 13 years of age."""
    today = timezone.now().date()
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )
    if age < 13:
        raise ValidationError("You must be at least 13 years old to use this service.")


class Profile(models.Model):
    """Profile model definition."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(_("description"), max_length=500, blank=True, null=True)
    location = models.CharField(_("location"), max_length=30, blank=True, null=True)
    birth_date = models.DateField(
        _("birth date"), null=True, blank=True, validators=[validate_age]
    )
    website = models.URLField(_("website"), max_length=200, blank=True, null=True)
    image = models.ImageField(null=True, blank=True, upload_to=profile_image_file_path)
    is_verified = models.BooleanField(_("verified"), default=False)
    is_suspended = models.BooleanField(default=False)

    @property
    def full_name(self):
        """Return a concatenation of the profile user's first and last names."""
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        """Return profile user's full name."""
        return self.full_name

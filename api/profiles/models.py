"""Profile app models."""
import os
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_age, validate_image_size

User = get_user_model()


def profile_image_file_path(instance, filename):
    """Generate file path for new profile image."""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    return os.path.join("uploads/profile/", filename)


class Profile(models.Model):
    """Profile model definition."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(_("description"), max_length=500, blank=True, null=True)
    location = models.CharField(_("location"), max_length=30, blank=True, null=True)
    birth_date = models.DateField(
        _("birth date"), null=True, blank=True, validators=[validate_age]
    )
    website = models.URLField(_("website"), max_length=200, blank=True, null=True)
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=profile_image_file_path,
        validators=[validate_image_size],
    )
    is_verified = models.BooleanField(_("verified"), default=False)
    is_suspended = models.BooleanField(default=False)

    @property
    def full_name(self):
        """Return a concatenation of the profile user's first and last names."""
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        """Return profile user's full name."""
        return self.full_name

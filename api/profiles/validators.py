"""validators for the profile app."""
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_image_size(file):
    """Ensure that the maximum size of the file being uploaded is 1MB."""
    max_size_kb = 1024
    if file.size > max_size_kb * 1024:
        raise ValidationError(
            f"The image cannot be larger than {int(max_size_kb)//1024}MB."
        )


def validate_age(value):
    """Ensure user is at least 13 years of age."""
    today = timezone.now().date()
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )
    if age < 13:
        raise ValidationError("You must be at least 13 years old to use Nexus.")

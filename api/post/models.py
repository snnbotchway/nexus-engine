"""Models for the post app."""
from django.db import models
from profiles.models import Profile


class Post(models.Model):
    """Post model definition."""

    content = models.CharField(max_length=280, null=True, blank=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    original_post = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="reposts"
    )

    def __str__(self):
        """Return part of content and author name."""
        return f'{self.content[:10]}... by "{self.author.full_name}"'

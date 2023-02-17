"""Serializers for the Profiles app."""
from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the profile model."""

    user_id = serializers.IntegerField()

    class Meta:
        """Serializer Meta class."""

        model = Profile
        fields = [
            "id",
            "user_id",
            "bio",
            "location",
            "birth_date",
            "website",
            "is_verified",
            "is_suspended",
            "image",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "is_suspended",
            "image",
        ]


class UserReadOnlyProfileSerializer(ProfileSerializer):
    """A profile serializer but with a read only user_id field."""

    user_id = serializers.IntegerField(read_only=True)

    def validate(self, attrs):
        """Raise error on create profile if one already exists."""
        request = self.context.get("request")
        profile_exists = Profile.objects.filter(user_id=request.user.id).exists()
        if profile_exists and request.method == "POST":
            raise serializers.ValidationError({"detail": "You already have a profile."})
        return attrs


class ProfileImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to profiles."""

    class Meta:
        """Image serializer meta class."""

        model = Profile
        fields = ["id", "image"]
        read_only_fields = ["id"]

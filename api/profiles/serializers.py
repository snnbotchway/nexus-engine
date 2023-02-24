"""Serializers for the Profiles app."""
from rest_framework import serializers

from .models import Follow, Profile


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


class CreateFollowSerializer(serializers.ModelSerializer):
    """Serializer for creating follows."""

    following_id = serializers.IntegerField()

    class Meta:
        """Follow serializer meta class."""

        model = Follow
        fields = [
            "id",
            "following_id",
            "follower_id",
        ]

    def validate_following_id(self, value):
        """Ensure `value` is a valid following ID for the current user's profile."""
        current_profile = self.context.get("current_profile")
        follow_exists = Follow.objects.filter(
            follower=current_profile, following_id=value
        ).exists()
        if follow_exists:
            raise serializers.ValidationError("You are already following this profile.")
        if current_profile.id == value:
            raise serializers.ValidationError("You cannot follow yourself.")
        return value

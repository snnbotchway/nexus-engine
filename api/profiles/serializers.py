"""Serializers for the Profiles app."""
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Follow, Profile

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    """Simple serializer for the user model."""

    class Meta:
        """Simple user serializer meta class."""

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
        ]


class SimpleUserSerializerWithDateJoined(SimpleUserSerializer):
    """SimpleUserSerializer with date_joined field included."""

    class Meta(SimpleUserSerializer.Meta):
        """Simple user serializer with date_joined meta class."""

        fields = SimpleUserSerializer.Meta.fields + [
            "date_joined",
        ]


class SimpleUserProfileSerializer(serializers.ModelSerializer):
    """Simple serializer for the profile model."""

    user = SimpleUserSerializer()
    is_following = serializers.BooleanField(required=False)
    follows_you = serializers.BooleanField(required=False)

    class Meta:
        """Simple User Profile serializer Meta class."""

        model = Profile
        fields = [
            "id",
            "user",
            "bio",
            "is_verified",
            "image",
            "is_following",
            "follows_you",
        ]


class UserProfileSerializer(SimpleUserProfileSerializer):
    """Serializer for the profile model."""

    user = SimpleUserSerializerWithDateJoined()
    following_count = serializers.IntegerField(required=False)
    followers_count = serializers.IntegerField(required=False)

    class Meta(SimpleUserProfileSerializer.Meta):
        """User Profile serializer Meta class."""

        fields = SimpleUserProfileSerializer.Meta.fields + [
            "birth_date",
            "location",
            "website",
            "is_suspended",
            "following_count",
            "followers_count",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for the profile model."""

    user_id = serializers.IntegerField(read_only=True)

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

    def validate(self, attrs):
        """Raise error on create profile if one already exists."""
        request = self.context.get("request")
        if request.method == "POST":
            profile_exists = Profile.objects.filter(user_id=request.user.id).exists()
            if profile_exists:
                raise serializers.ValidationError(
                    {"detail": "You already have a profile."}
                )
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
        get_object_or_404(Profile, id=value)
        current_profile = self.context.get("current_profile")
        follow_exists = Follow.objects.filter(
            follower=current_profile, following_id=value
        ).exists()
        if follow_exists:
            raise serializers.ValidationError("You are already following this profile.")
        if current_profile.id == value:
            raise serializers.ValidationError("You cannot follow yourself.")
        return value

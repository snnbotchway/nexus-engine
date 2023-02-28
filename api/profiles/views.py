"""Views for the Profiles app."""
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Follow, Profile
from .serializers import (
    CreateFollowSerializer,
    ProfileImageSerializer,
    ProfileSerializer,
    UserProfileSerializer,
)


class ProfileViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """The Profile view set."""

    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]

    def get_current_profile(self):
        """Return the current user's profile."""
        user = self.request.user
        if user.is_anonymous:
            return None
        if not hasattr(self, "_current_profile"):
            self._current_profile = Profile.objects.filter(user=user).first()
        return self._current_profile

    def get_permissions(self):
        """Allow anyone to get a profile."""
        if self.action == "retrieve":
            return [AllowAny()]
        return super().get_permissions()

    def get_object(self):
        """Add and return the profile object with additional fields if necessary."""
        if self.action == "me":
            if self.request.method == "DELETE":
                return get_object_or_404(Profile, user=self.request.user)
            profile, _ = Profile.objects.get_or_create(user=self.request.user)
            return profile
        elif self.action == "retrieve":
            instance = super().get_object()
            current_profile = self.get_current_profile()

            if current_profile is None:
                return instance

            # Add is_following and follows_you fields if current user is authenticated
            # and has a profile:
            follows_filter = {"pk": instance.pk}
            instance.is_following = current_profile.follows.filter(
                **follows_filter
            ).exists()
            instance.follows_you = current_profile.followed_by.filter(
                **follows_filter
            ).exists()

            return instance
        return super().get_object()

    def get_serializer_class(self):
        """Return appropriate serializer considering the action."""
        if self.action == "retrieve":
            return UserProfileSerializer
        elif self.action == "upload_image":
            return ProfileImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Set user to current user before creating profile."""
        serializer.save(user=self.request.user)

    @action(
        detail=False,
        methods=[
            "DELETE",
            "GET",
            "OPTIONS",
            "PATCH",
        ],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Me action to manage current user's profile."""
        if request.method == "GET":
            serializer = self.get_serializer(self.get_object())
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PATCH":
            serializer = self.get_serializer(self.get_object(), data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            self.get_object().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["POST"],
        detail=False,
        url_path="upload-image",
        permission_classes=[IsAuthenticated],
    )
    def upload_image(self, request, pk=None):
        """Upload an image to current user's profile."""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class FollowViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """Viewset for creating and deleting follow objects(follow and unfollow)."""

    queryset = Follow.objects.all()
    serializer_class = CreateFollowSerializer
    permission_classes = [IsAuthenticated]

    def get_current_profile(self):
        """Return the current user's profile."""
        if not hasattr(self, "_current_profile"):
            self._current_profile = Profile.objects.get(user=self.request.user)
        return self._current_profile

    def get_object(self):
        """Return the follow object for the current user and requested profile."""
        following_id = self.kwargs.get("pk")
        follow = get_object_or_404(
            Follow, follower=self.get_current_profile(), following_id=following_id
        )
        return follow

    def get_serializer_context(self):
        """Pass the current user's profile to the serializer."""
        return {"current_profile": self.get_current_profile()}

    def perform_create(self, serializer):
        """Set follower to current user's profile before saving."""
        serializer.save(follower=self.get_current_profile())

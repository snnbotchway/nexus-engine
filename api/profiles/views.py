"""Views for the Profiles app."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import Follow, Profile
from .serializers import (
    CreateFollowSerializer,
    ProfileImageSerializer,
    ProfileSerializer,
    UserReadOnlyProfileSerializer,
)


class ProfileViewSet(ModelViewSet):
    """The Profile view set."""

    http_method_names = [
        "delete",
        "get",
        "head",
        "options",
        "patch",
        "post",
    ]

    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """Return appropriate serializer considering the request method."""
        serializer_classes = {
            "PATCH": UserReadOnlyProfileSerializer,
            "me": UserReadOnlyProfileSerializer,
            "upload_image": ProfileImageSerializer,
            "admin_upload_image": ProfileImageSerializer,
        }
        method = self.request.method
        action = self.action
        serializer_class = self.serializer_class

        if method in serializer_classes:
            serializer_class = serializer_classes[method]
        elif action in serializer_classes:
            serializer_class = serializer_classes[action]

        return serializer_class

    @action(
        detail=False,
        methods=["GET", "PATCH", "POST", "DELETE"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Me action to manage current user's profile."""
        if request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "GET":
            profile, _ = Profile.objects.get_or_create(user=request.user)
            serializer = self.get_serializer(profile, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PATCH":
            profile, _ = Profile.objects.get_or_create(user=request.user)
            serializer = self.get_serializer(profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            profile = get_object_or_404(Profile, user=request.user)
            profile.delete()
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

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def admin_upload_image(self, request, pk=None):
        """Upload an image to any profile."""
        profile, _ = Profile.objects.get_or_create(pk=pk)
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class FollowViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
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

"""Views for the Profiles app."""
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .helpers import ProfileViewSetHelper
from .models import Follow, Profile
from .serializers import (
    CreateFollowSerializer,
    ProfileImageSerializer,
    ProfileSerializer,
    SimpleUserProfileSerializer,
    UserProfileSerializer,
)


class ProfileViewSet(
    ProfileViewSetHelper,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """The Profile view set."""

    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]
    queryset = Profile.objects.all()

    def get_permissions(self):
        """Allow anyone to get a profile."""
        if self.action == "retrieve":
            return [AllowAny()]
        return super().get_permissions()

    def get_object(self):
        """Return the profile object the view is displaying."""
        if self.action == "retrieve":
            return self.get_retrieve_object()
        return super().get_object()

    def get_serializer_class(self):
        """Return appropriate serializer considering the action."""
        serializer_map = {
            "followers": SimpleUserProfileSerializer,
            "following": SimpleUserProfileSerializer,
            "followers_i_know": SimpleUserProfileSerializer,
            "retrieve": UserProfileSerializer,
            "upload_image": ProfileImageSerializer,
        }
        if self.action == "me" and self.request.method == "GET":
            return UserProfileSerializer
        return serializer_map.get(self.action, ProfileSerializer)

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
        current_profile = self.get_me_object()
        if request.method == "GET":
            serializer = self.get_serializer(current_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PATCH":
            serializer = self.get_serializer(current_profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            current_profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["GET"], detail=True, permission_classes=[IsAuthenticated])
    def followers(self, request, pk=None):
        """List followers of any profile."""
        followers = (
            Follow.objects.filter(following=self.get_object())
            .select_related("follower")
            .values_list("follower", flat=True)
        )
        return self.get_profiles_in_queryset(followers)

    @action(methods=["GET"], detail=True, permission_classes=[IsAuthenticated])
    def following(self, request, pk=None):
        """List following of any profile."""
        following = (
            Follow.objects.filter(follower=self.get_object())
            .select_related("following")
            .values_list("following", flat=True)
        )
        return self.get_profiles_in_queryset(following)

    @action(
        methods=["GET"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="followers-i-know",
    )
    def followers_i_know(self, request, pk=None):
        """List followers_i_know of any profile."""
        current_profile_following = (
            Follow.objects.filter(follower=self.get_current_profile())
            .select_related("following")
            .values_list("following", flat=True)
        )
        followers = (
            Follow.objects.filter(following=self.get_object())
            .select_related("follower")
            .values_list("follower", flat=True)
        )

        followers_i_know = followers.intersection(current_profile_following)
        return self.get_profiles_in_queryset(followers_i_know)

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

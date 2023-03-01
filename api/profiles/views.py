"""Views for the Profiles app."""
from django.db.models import BooleanField, Case, Exists, OuterRef, Value, When
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
    SimpleUserProfileSerializer,
    UserProfileSerializer,
)


class ProfileViewSetHelper:
    """Helper functions for the ProfileViewSet."""

    def add_follow_fields(self, instance, current_profile):
        """Add is_following and follows_you fields to instance."""
        if current_profile:
            follows_filter = {"pk": instance.pk}
            instance.is_following = current_profile.follows.filter(
                **follows_filter
            ).exists()
            instance.follows_you = current_profile.followed_by.filter(
                **follows_filter
            ).exists()
        return instance

    def add_follow_counts(self, instance):
        """Add following and followers counts to instance."""
        instance.following_count = instance.follows.count()
        instance.followers_count = instance.followed_by.count()
        return instance

    def get_profiles_with_follow_info(self):
        """Return a queryset of profiles annotated with follow information."""
        current_profile = self.get_current_profile()
        return Profile.objects.annotate(
            is_following=Case(
                When(pk=current_profile.pk, then=Value(None)),
                default=Exists(
                    Follow.objects.filter(
                        following=OuterRef("pk"),
                        follower=current_profile,
                    ),
                ),
                output_field=BooleanField(),
            ),
            follows_you=Case(
                When(pk=current_profile.pk, then=Value(None)),
                default=Exists(
                    Follow.objects.filter(
                        follower=OuterRef("pk"),
                        following=current_profile,
                    ),
                ),
                output_field=BooleanField(),
            ),
        )

    def get_current_profile(self):
        """Return the current user's profile."""
        user = self.request.user
        if user.is_anonymous:
            return None
        if not hasattr(self, "_current_profile"):
            self._current_profile = Profile.objects.filter(user=user).first()
        return self._current_profile

    def get_me_object(self):
        """Get the profile object for the "me" action."""
        if self.request.method == "DELETE":
            return get_object_or_404(Profile, user=self.request.user)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def get_retrieve_object(self):
        """Get the profile object for the "retrieve" action."""
        instance = super().get_object()
        current_profile = self.get_current_profile()

        # Return the instance right away without annotation if the current user
        # is viewing their own profile.
        if current_profile == instance:
            return instance

        instance = self.add_follow_fields(instance, current_profile)
        instance = self.add_follow_counts(instance)

        return instance

    def get_profiles_in_queryset(self, queryset):
        """Return all profiles whose id is in a specified queryset."""
        profiles = (
            self.get_profiles_with_follow_info()
            .select_related("user")
            .filter(id__in=queryset)
            .order_by("id")
        )

        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileViewSet(
    ProfileViewSetHelper,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """The Profile view set."""

    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]

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

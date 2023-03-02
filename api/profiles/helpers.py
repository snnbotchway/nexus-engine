"""Helpers for the profiles app."""
from django.db.models import BooleanField, Case, Exists, OuterRef, Value, When
from django.shortcuts import get_object_or_404

from .models import Follow, Profile


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

        # Add extra follow fields as long as the current user is not viewing
        # their own profile.
        if current_profile != instance:
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

        paginator = self.pagination_class()
        paginator.page_size = 40
        paginated_profiles = paginator.paginate_queryset(profiles, self.request)
        serializer = self.get_serializer(paginated_profiles, many=True)
        return paginator.get_paginated_response(serializer.data)

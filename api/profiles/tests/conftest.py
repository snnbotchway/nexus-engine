"""Profiles app test fixtures."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from profiles.models import Profile

User = get_user_model()


@pytest.fixture
def detail_url():
    """Return profile detail URL."""

    def _detail_url(profile_id):
        return reverse("profiles:profile-detail", args=[profile_id])

    return _detail_url


@pytest.fixture
def profile_payload():
    """Return sample profile information as a payload."""
    date_from_14_years_ago = timezone.now().date() - timezone.timedelta(days=365 * 14)
    payload = {
        "bio": "sample description",
        "location": "sample location",
        "birth_date": date_from_14_years_ago,
        "website": "https://some-website.com",
    }
    return payload


@pytest.fixture
def image_url():
    """Return profile image upload URL."""

    def _image_url(profile_id):
        return reverse("profiles:profile-admin-upload-image", args=[profile_id])

    return _image_url


@pytest.fixture
def follow_detail_url():
    """Return the follow detail URL."""

    def _follow_detail_url(follow_id):
        return reverse("profiles:follow-detail", args=[follow_id])

    return _follow_detail_url


@pytest.fixture
def sample_profile(sample_user):
    """Return a sample profile."""
    return baker.make(Profile, user=sample_user)


@pytest.fixture
def other_profile():
    """Return a sample profile."""
    return baker.make(Profile)


@pytest.fixture
def follow_payload(other_profile):
    """Return a sample follow payload."""
    return {"following_id": other_profile.id}


@pytest.fixture
def pop_extra_keys():
    """Pop is_following and follows_you from a dictionary."""

    def _pop_extra_keys(dictionary):
        keys = [
            "is_following",
            "follows_you",
            "followers_count",
            "following_count",
        ]
        for key in keys:
            if key in dictionary:
                dictionary.pop(key)
        return dictionary

    return _pop_extra_keys


@pytest.fixture
def followers_list_url():
    """Return the followers list URL."""

    def _followers_list_url(profile_id):
        return reverse("profiles:profile-followers", args=[profile_id])

    return _followers_list_url


@pytest.fixture
def following_list_url():
    """Return the following list URL."""

    def _following_list_url(profile_id):
        return reverse("profiles:profile-following", args=[profile_id])

    return _following_list_url


@pytest.fixture
def followers_i_know_list_url():
    """Return followers i know list URL."""

    def _followers_i_know_list_url(profile_id):
        return reverse("profiles:profile-followers-i-know", args=[profile_id])

    return _followers_i_know_list_url

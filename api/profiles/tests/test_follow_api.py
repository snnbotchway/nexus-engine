"""Tests for the Follow API."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from model_bakery import baker
from profiles.models import Follow, Profile
from profiles.serializers import CreateFollowSerializer
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()
FOLLOW_URL = reverse("profiles:follow-list")


@pytest.fixture
def api_client():
    """Return an API client object."""
    return APIClient()


@pytest.fixture
def not_allowed_response():
    """Return the method not allowed error response."""

    def _not_allowed_response(method):
        return {"detail": f'Method "{method}" not allowed.'}

    return _not_allowed_response


@pytest.fixture
def follow_detail_url():
    """Return the follow detail URL."""

    def _follow_detail_url(follow_id):
        return reverse("profiles:follow-detail", args=[follow_id])

    return _follow_detail_url


@pytest.fixture
def sample_user():
    """Return a sample user."""
    return baker.make(User)


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


@pytest.mark.django_db
class TestCreateFollow:
    """Test creating a follow object."""

    def test_follow_other_profile_returns_201(
        self, api_client, follow_payload, sample_user, sample_profile
    ):
        """Test create follow successful."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(FOLLOW_URL, follow_payload)

        follow = Follow.objects.get(pk=response.data.get("id"))
        serializer = CreateFollowSerializer(follow)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == serializer.data
        assert follow.follower == sample_profile
        assert follow.following.id == follow_payload.get("following_id")
        assert Follow.objects.count() == 1

    def test_follow_profile_more_than_once_returns_400(
        self, api_client, follow_payload, sample_user, sample_profile
    ):
        """Test follow profile more than once returns error."""
        api_client.force_authenticate(user=sample_user)
        baker.make(Follow, follower=sample_profile, **follow_payload)

        response = api_client.post(FOLLOW_URL, follow_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "following_id": ["You are already following this profile."]
        }
        assert Follow.objects.count() == 1

    def test_follow_oneself_returns_400(
        self, api_client, sample_user, sample_profile, follow_payload
    ):
        """Test follow oneself returns error."""
        api_client.force_authenticate(user=sample_user)
        follow_payload.update({"following_id": sample_profile.id})

        response = api_client.post(FOLLOW_URL, follow_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"following_id": ["You cannot follow yourself."]}
        assert Follow.objects.count() == 0

    def test_anonymous_user_follow_returns_401(self, api_client, follow_payload):
        """Test anonymous users cannot follow others."""

        response = api_client.post(FOLLOW_URL, follow_payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Follow.objects.count() == 0


@pytest.mark.django_db
class TestRetrieveFollow:
    """Test retrieve follow."""

    def test_get_follow_list_returns_405(
        self, api_client, not_allowed_response, sample_user
    ):
        """Test get follow list not allowed."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.get(FOLLOW_URL)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == not_allowed_response("GET")

    def test_get_follow_detail_returns_405(
        self, api_client, follow_detail_url, not_allowed_response, sample_user
    ):
        """Test get follow detail not allowed."""
        api_client.force_authenticate(user=sample_user)
        follow = baker.make(Follow)
        url = follow_detail_url(follow.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == not_allowed_response("GET")


@pytest.mark.django_db
class TestUpdateFollow:
    """Test update follow."""

    def test_partial_update_follow_returns_405(
        self,
        api_client,
        follow_detail_url,
        follow_payload,
        not_allowed_response,
        sample_user,
    ):
        """Test partial update follow not allowed."""
        api_client.force_authenticate(user=sample_user)
        follow = baker.make(Follow)
        url = follow_detail_url(follow.id)

        response = api_client.patch(url, follow_payload)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == not_allowed_response("PATCH")

    def test_full_update_follow_returns_405(
        self,
        api_client,
        follow_detail_url,
        follow_payload,
        not_allowed_response,
        sample_user,
    ):
        """Test full update follow not allowed."""
        api_client.force_authenticate(user=sample_user)
        follow = baker.make(Follow)
        url = follow_detail_url(follow.id)

        response = api_client.put(url, follow_payload)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == not_allowed_response("PUT")


@pytest.mark.django_db
class TestDeleteFollow:
    """Test deleting a follow object."""

    def test_unfollow_profile_returns_204(
        self, api_client, sample_profile, sample_user, follow_detail_url
    ):
        """Test unfollow profile successful."""
        follow = baker.make(Follow, follower=sample_profile)
        url = follow_detail_url(follow.id)
        api_client.force_authenticate(user=sample_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.data
        assert Follow.objects.count() == 0

    def test_delete_other_profiles_follow_returns_404(
        self, api_client, sample_user, follow_detail_url, other_profile, sample_profile
    ):
        """Test delete other profile's follow returns error."""
        follow = baker.make(Follow, follower=other_profile)
        url = follow_detail_url(follow.id)
        api_client.force_authenticate(user=sample_user)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"detail": "Not found."}
        assert Follow.objects.count() == 1

    def test_anonymous_user_unfollow_returns_401(
        self, api_client, follow_detail_url, sample_profile
    ):
        """Test anonymous user cannot unfollow."""
        follow = baker.make(Follow, follower=sample_profile)
        url = follow_detail_url(follow.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Follow.objects.count() == 1

"""Tests for the User API."""
import os
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from PIL import Image
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()
PROFILE_URL = reverse("profiles:profile-list")
PROFILE_ME_URL = reverse("profiles:profile-me")
PROFILE_IMAGE_URL = reverse("profiles:profile-upload-image")


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def detail_url():
    """Return profile detail URL."""

    def _detail_url(profile_id):
        return reverse("profiles:profile-detail", args=[profile_id])

    return _detail_url


@pytest.fixture
def admin_user():
    """Create and return an admin user."""
    return baker.make(User, is_staff=True)


@pytest.fixture
def sample_user():
    """Create and return a sample user."""
    return baker.make(User)


@pytest.fixture
def profile_payload():
    """Return sample profile information as a payload."""

    def _profile_payload(user_id=None):
        date_from_14_years_ago = timezone.now().date() - timezone.timedelta(
            days=365 * 14
        )
        payload = {
            "bio": "sample description",
            "location": "sample location",
            "birth_date": date_from_14_years_ago,
            "website": "https://some-website.com",
        }
        if user_id is None:
            return payload
        payload.update({"user_id": user_id})
        return payload

    return _profile_payload


@pytest.fixture
def image_url():
    """Return profile image upload URL."""

    def _image_url(profile_id):
        return reverse("profiles:profile-admin-upload-image", args=[profile_id])

    return _image_url


@pytest.fixture
def sample_profile():
    """Return sample profile."""
    return baker.make(Profile)


@pytest.mark.django_db
class TestAdminCreateProfile:
    """Test the admin create profile endpoint."""

    def test_admin_create_profile_returns_201(
        self, admin_user, api_client, profile_payload, sample_user
    ):
        """Test admins can create profiles user profiles."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(PROFILE_URL, profile_payload(sample_user.id))

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.all().count() == 1

    def test_admin_create_profile_without_required_fields_returns_201(
        self, admin_user, api_client, sample_user
    ):
        """Test admin can create profile for others."""
        api_client.force_authenticate(user=admin_user)
        payload = {"user_id": sample_user.id}

        response = api_client.post(PROFILE_URL, payload)

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.all().count() == 1

    def test_admin_create_profile_without_user_id_returns_400(
        self, admin_user, api_client, profile_payload, sample_user
    ):
        """Test admin create profile without user_id returns error."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(PROFILE_URL, profile_payload())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"user_id": ["This field is required."]}
        assert Profile.objects.all().count() == 0

    def test_admin_create_profile_under_13_returns_400(
        self, admin_user, api_client, profile_payload, sample_user
    ):
        """Test admin create profile with age under 13 returns an error."""
        api_client.force_authenticate(user=admin_user)
        date_from_12_years_ago = timezone.now().date() - timezone.timedelta(
            days=365 * 12
        )
        payload = profile_payload(sample_user.id)
        payload.update({"birth_date": date_from_12_years_ago})

        response = api_client.post(PROFILE_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "birth_date": ["You must be at least 13 years old to use Nexus."]
        }
        assert Profile.objects.all().count() == 0

    def test_admin_create_profile_with_invalid_website_returns_400(
        self, admin_user, api_client, profile_payload, sample_user
    ):
        """Test admin create profile with invalid website returns an error."""
        api_client.force_authenticate(user=admin_user)
        payload = profile_payload(sample_user.id)
        payload.update({"website": "invalid url"})

        response = api_client.post(PROFILE_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"website": ["Enter a valid URL."]}
        assert Profile.objects.all().count() == 0

    def test_authenticated_but_not_admin_create_profile_returns_403(
        self, api_client, profile_payload, sample_user
    ):
        """Test authenticated user who isn't admin create profile returns an error."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(PROFILE_URL, profile_payload(sample_user.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }
        assert Profile.objects.all().count() == 0

    def test_anonymous_user_create_profile_returns_401(
        self, api_client, profile_payload, sample_user
    ):
        """Test anonymous user create profile returns an error."""
        response = api_client.post(PROFILE_URL, profile_payload(sample_user.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 0


@pytest.mark.django_db
class TestAdminListProfiles:
    """Test the list profile endpoint that's only accessible by admins."""

    def test_admin_retrieve_profile_list_returns_200(self, admin_user, api_client):
        """Test admin can retrieve profile list."""
        api_client.force_authenticate(user=admin_user)
        baker.make(Profile, _quantity=3)

        response = api_client.get(PROFILE_URL)

        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        assert response.data == serializer.data
        assert len(response.data) == 3
        assert response.status_code == status.HTTP_200_OK
        assert Profile.objects.all().count() == 3

    def test_authenticated_but_not_admin_retrieve_profile_list_returns_403(
        self, api_client, sample_user
    ):
        """Test authenticated but not admin retrieve profile list returns error."""
        api_client.force_authenticate(user=sample_user)
        baker.make(Profile, _quantity=3)

        response = api_client.get(PROFILE_URL)

        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        assert response.data != serializer.data
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }
        assert Profile.objects.all().count() == 3

    def test_anonymous_user_retrieve_profile_list_returns_401(self, api_client):
        """Test anonymous user retrieve profile list returns error."""
        baker.make(Profile, _quantity=3)

        response = api_client.get(PROFILE_URL)

        profiles = Profile.objects.all()
        serializer = ProfileSerializer(profiles, many=True)
        assert response.data != serializer.data
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 3


@pytest.mark.django_db
class TestAdminRetrieveProfileDetail:
    """Test the profile detail endpoint that's only accessible by admins."""

    def test_admin_retrieve_profile_detail_returns_200(
        self, admin_user, api_client, detail_url
    ):
        """Test admin can retrieve profile detail."""
        api_client.force_authenticate(user=admin_user)
        profile = baker.make(Profile)

        response = api_client.get(detail_url(profile.id))

        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert Profile.objects.all().count() == 1

    def test_authenticated_but_not_admin_retrieve_profile_detail_returns_403(
        self, api_client, detail_url, sample_user
    ):
        """Test authenticated but not admin retrieve profile detail returns error."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile)

        response = api_client.get(detail_url(profile.id))

        serializer = ProfileSerializer(profile)
        assert response.data != serializer.data
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_retrieve_profile_detail_returns_401(
        self, api_client, detail_url
    ):
        """Test anonymous user retrieve profile detail returns error."""
        profile = baker.make(Profile)

        response = api_client.get(detail_url(profile.id))

        serializer = ProfileSerializer(profile)
        assert response.data != serializer.data
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestAdminUpdateProfile:
    """Test the profile update endpoint that's only accessible by admins."""

    def test_admin_update_profile_returns_200(
        self, admin_user, api_client, detail_url, profile_payload, sample_user
    ):
        """Test admin can update a profile but not change it's user."""
        api_client.force_authenticate(user=admin_user)
        profile = baker.make(Profile, user=sample_user)
        another_user = baker.make(User)
        payload = profile_payload(another_user.id)

        response = api_client.patch(detail_url(profile.id), payload)

        profile.refresh_from_db()
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.bio == payload.get("bio")
        assert profile.birth_date == payload.get("birth_date")
        assert profile.website == payload.get("website")
        assert profile.location == payload.get("location")
        assert Profile.objects.all().count() == 1

        # assert profile's user is not changed
        assert profile.user == sample_user

    def test_admin_full_update_profile_returns_405(
        self, admin_user, api_client, detail_url, profile_payload, sample_user
    ):
        """Test admin cannot fully update a user profile."""
        api_client.force_authenticate(user=admin_user)
        old_payload = {
            "bio": "old bio",
            "website": "https://old-website.com",
            "location": "old location",
            "birth_date": "1999-01-01",
        }
        profile = baker.make(Profile, **old_payload)
        new_payload = profile_payload(sample_user.id)

        response = api_client.put(detail_url(profile.id), new_payload)

        profile.refresh_from_db()
        assert response.data == {"detail": 'Method "PUT" not allowed.'}
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_authenticated_but_not_admin_update_profile_returns_403(
        self, api_client, detail_url, profile_payload, sample_user
    ):
        """Test authenticated but not admin cannot update a user profile."""
        api_client.force_authenticate(user=sample_user)
        old_payload = {
            "bio": "old bio",
            "website": "https://old-website.com",
            "location": "old location",
            "birth_date": "1999-01-01",
        }
        profile = baker.make(Profile, **old_payload)
        new_payload = profile_payload(sample_user.id)

        response = api_client.patch(detail_url(profile.id), new_payload)

        profile.refresh_from_db()
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }
        assert response.status_code == status.HTTP_403_FORBIDDEN
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_update_profile_returns_401(
        self, api_client, detail_url, profile_payload, sample_user
    ):
        """Test anonymous user cannot update a user profile."""
        old_payload = {
            "bio": "old bio",
            "website": "https://old-website.com",
            "location": "old location",
            "birth_date": "1999-01-01",
        }
        profile = baker.make(Profile, **old_payload)
        new_payload = profile_payload(sample_user.id)

        response = api_client.patch(detail_url(profile.id), new_payload)

        profile.refresh_from_db()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestAdminDeleteProfile:
    """Test the profile delete endpoint that's only accessible by admins."""

    def test_admin_delete_profile_returns_204(self, admin_user, api_client, detail_url):
        """Test admin can delete profile."""
        api_client.force_authenticate(user=admin_user)
        profile = baker.make(Profile)

        response = api_client.delete(detail_url(profile.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.data
        assert Profile.objects.all().count() == 0

    def test_authenticated_but_not_admin_delete_profile_returns_403(
        self, api_client, detail_url, sample_user
    ):
        """Test authenticated but not admin delete profile returns error."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile)

        response = api_client.delete(detail_url(profile.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_delete_profile_returns_401(self, api_client, detail_url):
        """Test anonymous user delete profile returns error."""
        profile = baker.make(Profile)

        response = api_client.delete(detail_url(profile.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestCreateProfileMe:
    """Test create profile on "me" endpoint."""

    def test_user_create_profile_returns_201(
        self, api_client, profile_payload, sample_user
    ):
        """Test authenticated user can create profile."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(PROFILE_ME_URL, profile_payload())

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_201_CREATED
        assert profile.user == sample_user
        assert Profile.objects.all().count() == 1

    def test_user_create_profile_without_required_fields_returns_201(
        self, api_client, sample_user
    ):
        """Test authenticated user can create profile without required fields."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(PROFILE_ME_URL, {})

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_201_CREATED
        assert profile.user == sample_user
        assert Profile.objects.all().count() == 1

    def test_user_create_profile_under_13_returns_400(
        self, api_client, profile_payload, sample_user
    ):
        """Test user create profile with age under 13 returns an error."""
        api_client.force_authenticate(user=sample_user)
        date_from_12_years_ago = timezone.now().date() - timezone.timedelta(
            days=365 * 12
        )
        payload = profile_payload()
        payload.update({"birth_date": date_from_12_years_ago})

        response = api_client.post(PROFILE_ME_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "birth_date": ["You must be at least 13 years old to use Nexus."]
        }
        assert Profile.objects.all().count() == 0

    def test_user_create_profile_with_invalid_website_returns_400(
        self, api_client, profile_payload, sample_user
    ):
        """Test user create profile with invalid website returns an error."""
        api_client.force_authenticate(user=sample_user)
        payload = profile_payload()
        payload.update({"website": "invalid url"})

        response = api_client.post(PROFILE_ME_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"website": ["Enter a valid URL."]}
        assert Profile.objects.all().count() == 0

    def test_anonymous_user_create_profile_returns_401(
        self, api_client, profile_payload
    ):
        """Test anonymous user create profile returns an error."""
        response = api_client.post(PROFILE_ME_URL, profile_payload())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 0


@pytest.mark.django_db
class TestRetrieveProfileMe:
    """Test retrieve profile on "me" endpoint."""

    def test_user_retrieve_profile_detail_returns_200(self, api_client, sample_user):
        """Test user can retrieve profile detail."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile, user=sample_user)

        response = api_client.get(PROFILE_ME_URL)

        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert Profile.objects.all().count() == 1

    def test_create_profile_for_user_if_not_exist_on_get_profile(
        self, api_client, sample_user
    ):
        """
        Test a profile is created if one does not exist for a user who tries to get
        their profile.
        """
        api_client.force_authenticate(user=sample_user)

        assert Profile.objects.all().count() == 0

        response = api_client.get(PROFILE_ME_URL)

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.user == sample_user
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_retrieve_profile_detail_returns_401(self, api_client):
        """Test anonymous user retrieve profile detail returns error."""
        profile = baker.make(Profile)

        response = api_client.get(PROFILE_ME_URL)

        serializer = ProfileSerializer(profile)
        assert response.data != serializer.data
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestUpdateProfileMe:
    """Test update profile on "me" endpoint."""

    def test_user_update_profile_returns_200(
        self, api_client, profile_payload, sample_user
    ):
        """Test authenticated user can update his profile."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile, user=sample_user)
        payload = profile_payload()

        response = api_client.patch(PROFILE_ME_URL, payload)

        profile.refresh_from_db()
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.user == sample_user
        assert profile.bio == payload.get("bio")
        assert profile.birth_date == payload.get("birth_date")
        assert profile.website == payload.get("website")
        assert profile.location == payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_create_profile_for_user_if_not_exist_on_update_profile(
        self, api_client, profile_payload, sample_user
    ):
        """
        Test a profile is created if one does not exist for a user who tries to update
        their profile.
        """
        api_client.force_authenticate(user=sample_user)

        assert Profile.objects.all().count() == 0

        payload = profile_payload()

        response = api_client.patch(PROFILE_ME_URL, payload)

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.user == sample_user
        assert profile.bio == payload.get("bio")
        assert profile.birth_date == payload.get("birth_date")
        assert profile.website == payload.get("website")
        assert profile.location == payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_user_full_update_profile_returns_405(
        self, api_client, profile_payload, sample_user
    ):
        """Test user cannot fully update profile."""
        api_client.force_authenticate(user=sample_user)
        old_payload = {
            "user_id": sample_user.id,
            "bio": "old bio",
            "website": "https://old-website.com",
            "location": "old location",
            "birth_date": "1999-01-01",
        }
        profile = baker.make(Profile, **old_payload)
        new_payload = profile_payload()

        response = api_client.put(PROFILE_ME_URL, new_payload)

        profile.refresh_from_db()
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == {"detail": 'Method "PUT" not allowed.'}
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_update_profile_returns_401(
        self, api_client, profile_payload, sample_user
    ):
        """Test anonymous user cannot update a user profile."""
        old_payload = {
            "user_id": sample_user.id,
            "bio": "old bio",
            "website": "https://old-website.com",
            "location": "old location",
            "birth_date": "1999-01-01",
        }
        profile = baker.make(Profile, **old_payload)
        new_payload = profile_payload()

        response = api_client.patch(PROFILE_ME_URL, new_payload)

        profile.refresh_from_db()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestDeleteProfileMe:
    """Test delete profile on "me" endpoint."""

    def test_user_delete_profile_returns_204(self, api_client, sample_user):
        """Test user can delete profile."""
        api_client.force_authenticate(user=sample_user)
        baker.make(Profile, user=sample_user)

        response = api_client.delete(PROFILE_ME_URL)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.data
        assert Profile.objects.all().count() == 0

    def test_anonymous_user_delete_profile_returns_401(self, api_client):
        """Test anonymous user delete profile returns error."""
        baker.make(Profile)

        response = api_client.delete(PROFILE_ME_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestAdminProfileImageUpload:
    """Test admin profile image upload endpoint."""

    def test_admin_upload_image_to_profile_returns_200(
        self, api_client, admin_user, image_url, sample_profile
    ):
        """Test uploading an image to a profile."""
        api_client.force_authenticate(user=admin_user)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                image_url(sample_profile.id), {"image": ntf}, format="multipart"
            )

        profile = Profile.objects.get(pk=response.data.get("id"))
        assert response.status_code == status.HTTP_200_OK
        assert "image" in response.data
        assert os.path.exists(profile.image.path)
        assert Profile.objects.count() == 1
        os.remove(profile.image.path)

    def test_upload_invalid_image_returns_400(
        self, api_client, admin_user, image_url, sample_profile
    ):
        """Test uploading an invalid image."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            image_url(sample_profile.id), {"image": "not_an_image"}, format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "image" in response.data

    def test_authenticated_but_not_admin_upload_image_returns_403(
        self, api_client, image_url, sample_profile, sample_user
    ):
        """Test authenticated but not admin user cannot upload profile image."""
        api_client.force_authenticate(user=sample_user)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                image_url(sample_profile.id), {"image": ntf}, format="multipart"
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }

    def test_anonymous_user_upload_profile_image_returns_401(
        self, api_client, image_url, sample_profile
    ):
        """Test anonymous user cannot upload profile image."""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                image_url(sample_profile.id), {"image": ntf}, format="multipart"
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }


@pytest.mark.django_db
class TestProfileImageUpload:
    """Test profile image upload endpoint."""

    def test_upload_image_to_profile_returns_200(self, api_client, sample_user):
        """Test uploading an image to profile."""
        api_client.force_authenticate(user=sample_user)
        baker.make(Profile, user=sample_user)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                PROFILE_IMAGE_URL, {"image": ntf}, format="multipart"
            )

        profile = Profile.objects.get(pk=response.data.get("id"))
        assert response.status_code == status.HTTP_200_OK
        assert "image" in response.data
        assert os.path.exists(profile.image.path)
        assert Profile.objects.count() == 1
        os.remove(profile.image.path)

    def test_profile_created_if_not_exists_on_image_upload(
        self, api_client, sample_user
    ):
        """Test profile is created if not exists on image upload."""
        api_client.force_authenticate(user=sample_user)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                PROFILE_IMAGE_URL, {"image": ntf}, format="multipart"
            )

        profile = Profile.objects.get(pk=response.data.get("id"))
        assert response.status_code == status.HTTP_200_OK
        assert "image" in response.data
        assert os.path.exists(profile.image.path)
        assert Profile.objects.count() == 1
        os.remove(profile.image.path)

    def test_upload_invalid_image_returns_400(self, api_client, sample_user):
        """Test uploading an invalid image."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(
            PROFILE_IMAGE_URL, {"image": "not_an_image"}, format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "image" in response.data

    def test_anonymous_user_upload_profile_image_returns_401(self, api_client):
        """Test anonymous user cannot upload profile image."""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                PROFILE_IMAGE_URL, {"image": ntf}, format="multipart"
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == {
            "detail": "Authentication credentials were not provided."
        }

"""Tests for the Profile API."""
import os
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from PIL import Image
from profiles.models import Follow, Profile
from profiles.serializers import (
    ProfileSerializer,
    SimpleUserProfileSerializer,
    UserProfileSerializer,
)
from rest_framework import status

User = get_user_model()
PROFILE_URL = reverse("profiles:profile-list")
PROFILE_ME_URL = reverse("profiles:profile-me")
PROFILE_IMAGE_URL = reverse("profiles:profile-upload-image")


@pytest.mark.django_db
class TestCreateProfile:
    """Test the user create profile endpoint."""

    def test_user_create_profile_returns_201(
        self, api_client, profile_payload, sample_user
    ):
        """Test users can create profile."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(PROFILE_URL, profile_payload)

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.all().count() == 1

    def test_user_create_profile_if_exists_returns_400(
        self, api_client, profile_payload, sample_user
    ):
        """Test users cannot create a second profile."""
        baker.make(Profile, user=sample_user)
        api_client.force_authenticate(user=sample_user)

        response = api_client.post(PROFILE_URL, profile_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"detail": ["You already have a profile."]}
        assert Profile.objects.all().count() == 1

    def test_user_create_profile_under_13_returns_400(
        self, sample_user, api_client, profile_payload
    ):
        """Test user create profile with age under 13 returns an error."""
        api_client.force_authenticate(user=sample_user)
        date_from_12_years_ago = timezone.now().date() - timezone.timedelta(
            days=365 * 12
        )
        profile_payload.update({"birth_date": date_from_12_years_ago})

        response = api_client.post(PROFILE_URL, profile_payload)

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
        profile_payload.update({"website": "invalid url"})

        response = api_client.post(PROFILE_URL, profile_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"website": ["Enter a valid URL."]}
        assert Profile.objects.all().count() == 0

    def test_anonymous_user_create_profile_returns_401(
        self, api_client, profile_payload, unauthorized_response
    ):
        """Test anonymous user create profile returns an error."""
        response = api_client.post(PROFILE_URL, profile_payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        assert Profile.objects.all().count() == 0


@pytest.mark.django_db
class TestRetrieveProfile:
    """Test the retrieve profile endpoint."""

    def test_get_profile_list_returns_405(
        self,
        api_client,
        not_allowed_response,
        sample_user,
    ):
        """Test get profile list not allowed."""
        api_client.force_authenticate(user=sample_user)
        baker.make(Profile, _quantity=3)

        response = api_client.get(PROFILE_URL)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == not_allowed_response("GET")
        assert Profile.objects.all().count() == 3

    def test_anonymous_user_retrieve_profile_detail_returns_200(
        self,
        api_client,
        detail_url,
        pop_extra_keys,
    ):
        """Test anyone can retrieve any profile."""
        profile = baker.make(Profile)

        response = api_client.get(detail_url(profile.id))

        assert response.status_code == status.HTTP_200_OK
        assert Profile.objects.all().count() == 1
        assert "is_following" not in response.data
        assert "follows_you" not in response.data
        assert response.data.get("following_count") == 0
        assert response.data.get("followers_count") == 0
        assert len(response.data.get("user")) == 4

        # pop following and followers count fields for serializer.data comparison:
        response.data = pop_extra_keys(response.data)
        serializer = UserProfileSerializer(profile)
        assert response.data == serializer.data

    def test_is_following_field(
        self, api_client, detail_url, pop_extra_keys, sample_profile, sample_user
    ):
        """Test is_following field on get profile."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile)
        sample_profile.follows.add(profile)

        response = api_client.get(detail_url(profile.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("is_following")
        assert not response.data.get("follows_you")
        assert response.data.get("following_count") == 0
        assert response.data.get("followers_count") == 1
        assert Profile.objects.all().count() == 2
        assert Follow.objects.count() == 1

        # pop the extra keys for serializer.data comparison:
        response.data = pop_extra_keys(response.data)
        serializer = UserProfileSerializer(profile)
        assert response.data == serializer.data

    def test_follows_you_field(
        self, api_client, detail_url, pop_extra_keys, sample_profile, sample_user
    ):
        """Test follows_you fields on get profile."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile)
        sample_profile.followed_by.add(profile)

        response = api_client.get(detail_url(profile.id))

        assert response.status_code == status.HTTP_200_OK
        assert not response.data.get("is_following")
        assert response.data.get("follows_you")
        assert response.data.get("following_count") == 1
        assert response.data.get("followers_count") == 0
        assert Profile.objects.all().count() == 2
        assert Follow.objects.count() == 1

        # pop the extra keys for serializer.data comparison:
        serializer = UserProfileSerializer(profile)
        response.data = pop_extra_keys(response.data)
        assert response.data == serializer.data

    def test_is_following_and_follows_you_fields(
        self, api_client, detail_url, pop_extra_keys, sample_profile, sample_user
    ):
        """Test is_following and follows_you fields on get profile."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile)
        sample_profile.follows.add(profile)
        sample_profile.followed_by.add(profile)

        response = api_client.get(detail_url(profile.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("is_following")
        assert response.data.get("follows_you")
        assert response.data.get("following_count") == 1
        assert response.data.get("followers_count") == 1
        assert Profile.objects.all().count() == 2
        assert Follow.objects.count() == 2

        # pop the extra keys for serializer.data comparison:
        serializer = UserProfileSerializer(profile)
        response.data = pop_extra_keys(response.data)
        assert response.data == serializer.data


@pytest.mark.django_db
class TestRetrieveProfileMe:
    """Test retrieve current user profile."""

    def test_user_retrieve_profile_detail_returns_200(
        self, api_client, sample_user, sample_profile
    ):
        """Test user can retrieve profile detail."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.get(PROFILE_ME_URL)

        serializer = UserProfileSerializer(sample_profile)
        assert response.data == serializer.data
        assert not response.data.get("is_following")
        assert not response.data.get("follows_you")
        assert len(response.data.get("user")) == 4
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
        serializer = UserProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.user == sample_user
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_retrieve_profile_detail_returns_401(
        self, api_client, unauthorized_response
    ):
        """Test anonymous user retrieve profile detail returns error."""
        profile = baker.make(Profile)

        response = api_client.get(PROFILE_ME_URL)

        serializer = ProfileSerializer(profile)
        assert response.data != serializer.data
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestUpdateProfileMe:
    """Test update current user's profile."""

    def test_user_update_profile_returns_200(
        self, api_client, profile_payload, sample_user
    ):
        """Test authenticated user can update his profile."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile, user=sample_user)

        response = api_client.patch(PROFILE_ME_URL, profile_payload)

        profile.refresh_from_db()
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.user == sample_user
        assert profile.bio == profile_payload.get("bio")
        assert profile.birth_date == profile_payload.get("birth_date")
        assert profile.website == profile_payload.get("website")
        assert profile.location == profile_payload.get("location")
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

        response = api_client.patch(PROFILE_ME_URL, profile_payload)

        profile = Profile.objects.get(pk=response.data.get("id"))
        serializer = ProfileSerializer(profile)
        assert response.data == serializer.data
        assert response.status_code == status.HTTP_200_OK
        assert profile.user == sample_user
        assert profile.bio == profile_payload.get("bio")
        assert profile.birth_date == profile_payload.get("birth_date")
        assert profile.website == profile_payload.get("website")
        assert profile.location == profile_payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_user_full_update_profile_returns_405(
        self, api_client, profile_payload, not_allowed_response, sample_user
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
        new_payload = profile_payload

        response = api_client.put(PROFILE_ME_URL, new_payload)

        profile.refresh_from_db()
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.data == not_allowed_response("PUT")
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1

    def test_anonymous_user_update_profile_returns_401(
        self, api_client, profile_payload, sample_user, unauthorized_response
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
        new_payload = profile_payload

        response = api_client.patch(PROFILE_ME_URL, new_payload)

        profile.refresh_from_db()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        profile.bio = old_payload.get("bio")
        profile.birth_date = old_payload.get("birth_date")
        profile.website = old_payload.get("website")
        profile.location = old_payload.get("location")
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestDeleteProfileMe:
    """Test delete current user profile."""

    def test_user_delete_profile_returns_204(
        self, api_client, sample_user, sample_profile
    ):
        """Test user can delete profile."""
        api_client.force_authenticate(user=sample_user)
        assert Profile.objects.all().count() == 1

        response = api_client.delete(PROFILE_ME_URL)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.data
        assert Profile.objects.all().count() == 0

    def test_user_delete_non_existent_profile_404(
        self, api_client, not_found_response, sample_user
    ):
        """Test user delete profile returns error if profile does not exist."""
        api_client.force_authenticate(user=sample_user)
        assert Profile.objects.all().count() == 0

        response = api_client.delete(PROFILE_ME_URL)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == not_found_response
        assert Profile.objects.all().count() == 0

    def test_anonymous_user_delete_profile_returns_401(
        self, api_client, unauthorized_response
    ):
        """Test anonymous user delete profile returns error."""
        baker.make(Profile)

        response = api_client.delete(PROFILE_ME_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        assert Profile.objects.all().count() == 1


@pytest.mark.django_db
class TestRetrieveFollowLists:
    """Test list a profile's followers/following."""

    def test_list_a_profiles_followers_returns_200(
        self,
        api_client,
        followers_list_url,
        other_profile,
        pop_extra_keys,
        sample_profile,
        sample_user,
    ):
        """Test retrieve list of profiles; following a profile."""
        baker.make(Profile)
        profile = baker.make(Profile)
        other_profile.followed_by.add(profile)
        other_profile.followed_by.add(sample_profile)
        url = followers_list_url(other_profile.id)
        api_client.force_authenticate(user=sample_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == Follow.objects.count() == 2
        assert Profile.objects.count() == 4
        for follower in response.data:
            assert len(follower.get("user")) == 3
            assert follower.get("id") in [profile.id, sample_profile.id]
            assert not follower.get("follows_you")
            assert not follower.get("is_following")

            # pop is_following and follows_you for serializer.data comparison:
            follower = pop_extra_keys(follower)

        followers = other_profile.followed_by.all().order_by("id")
        serializer = SimpleUserProfileSerializer(followers, many=True)
        assert response.data == serializer.data

    def test_anonymous_user_list_a_profiles_followers_returns_401(
        self,
        api_client,
        followers_list_url,
        sample_profile,
        unauthorized_response,
    ):
        """Test anonymous user list profile followers returns error."""
        url = followers_list_url(sample_profile.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        assert Profile.objects.count() == 1

    def test_list_a_profiles_following_returns_200(
        self,
        api_client,
        following_list_url,
        other_profile,
        pop_extra_keys,
        sample_profile,
        sample_user,
    ):
        """Test retrieve list of profiles; a profile is following."""
        baker.make(Profile)
        profile = baker.make(Profile)
        other_profile.follows.add(profile)
        other_profile.follows.add(sample_profile)
        url = following_list_url(other_profile.id)
        api_client.force_authenticate(user=sample_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == Follow.objects.count() == 2
        assert Profile.objects.count() == 4

        for follower in response.data:
            assert follower.get("id") in [profile.id, sample_profile.id]
            assert not follower.get("follows_you")
            assert not follower.get("is_following")

            # pop is_following and follows_you for serializer.data comparison:
            follower = pop_extra_keys(follower)

        following = other_profile.follows.all().order_by("id")
        serializer = SimpleUserProfileSerializer(following, many=True)
        assert response.data == serializer.data

    def test_anonymous_user_list_a_profiles_following_returns_401(
        self,
        api_client,
        following_list_url,
        sample_profile,
        unauthorized_response,
    ):
        """Test anonymous user list profile following returns error."""
        url = following_list_url(sample_profile.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        assert Profile.objects.count() == 1

    def test_retrieve_profile_list_of_followers_i_know_returns_200(
        self,
        api_client,
        sample_profile,
        followers_i_know_list_url,
        other_profile,
        pop_extra_keys,
        sample_user,
    ):
        """
        Test retrieve list of profiles the current profile follows,
        among a profile's followers.
        """
        # Create 3 profiles:
        profile1 = baker.make(Profile)
        profile2 = baker.make(Profile)
        profile3 = baker.make(Profile)
        # They all follow other_profile:
        other_profile.followed_by.add(profile1)
        other_profile.followed_by.add(profile2)
        other_profile.followed_by.add(profile3)
        # Sample_profile follows profile1 and profile2 but not profile3:
        sample_profile.follows.add(profile1)
        sample_profile.follows.add(profile2)

        url = followers_i_know_list_url(other_profile.id)
        api_client.force_authenticate(user=sample_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert Follow.objects.count() == 5
        assert len(response.data) == 2
        profiles_i_follow = sample_profile.follows.all()
        followers_i_know = other_profile.followed_by.filter(
            id__in=profiles_i_follow
        ).order_by("id")
        for follower in response.data:
            assert follower.get("id") in [profile1.id, profile2.id]
            assert follower.get("id") != profile3.id
            assert not follower.get("follows_you")
            assert follower.get("is_following")

            # pop is_following and follows_you for serializer.data comparison:
            follower = pop_extra_keys(follower)

        serializer = SimpleUserProfileSerializer(followers_i_know, many=True)
        assert response.data == serializer.data

    def test_anonymous_user_list_profiles_i_know_returns_401(
        self,
        api_client,
        followers_i_know_list_url,
        sample_profile,
        unauthorized_response,
    ):
        """Test anonymous user list profile following returns error."""
        url = followers_i_know_list_url(sample_profile.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response
        assert Profile.objects.count() == 1


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

    def test_upload_large_image_to_profile_returns_400(self, api_client, sample_user):
        """Test uploading large image fails."""
        api_client.force_authenticate(user=sample_user)
        profile = baker.make(Profile, user=sample_user)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            # Create a file that is more than 1 MB
            large_file = SimpleUploadedFile("large_file.jpg", ntf.read() * 2000)

            # Attempt to upload the file and check that an error is returned
            response = api_client.post(
                PROFILE_IMAGE_URL, {"image": large_file}, format="multipart"
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"image": ["The image cannot be larger than 1MB."]}
        assert not profile.image

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
        assert response.data == {
            "image": [
                "The submitted data was not a file. Check the encoding type on the form."  # noqa
            ]
        }

    def test_anonymous_user_upload_profile_image_returns_401(
        self, api_client, unauthorized_response
    ):
        """Test anonymous user cannot upload profile image."""
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            response = api_client.post(
                PROFILE_IMAGE_URL, {"image": ntf}, format="multipart"
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data == unauthorized_response

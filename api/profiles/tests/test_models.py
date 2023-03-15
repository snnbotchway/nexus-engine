from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from model_bakery import baker
from profiles.models import Follow, Profile, profile_image_file_path

User = get_user_model()


@pytest.fixture
def sample_user():
    """Return a sample user."""
    return baker.make(User)


@pytest.fixture
def sample_payload():
    """Return sample user information as a payload."""
    date_from_14_years_ago = timezone.now().date() - timezone.timedelta(days=365 * 14)
    return {
        "bio": "sample description",
        "location": "sample location",
        "birth_date": date_from_14_years_ago,
        "website": "https://some-website.com",
    }


@pytest.mark.django_db
class TestProfileModel:
    def test_creating_a_profile_is_successful(self, sample_payload, sample_user):
        """Test that profiles are created successfully."""
        profile = Profile.objects.create(**sample_payload, user=sample_user)

        assert profile.user == sample_user
        assert profile.bio == sample_payload.get("bio")
        assert profile.location == sample_payload.get("location")
        assert profile.birth_date == sample_payload.get("birth_date")
        assert profile.website == sample_payload.get("website")
        assert not profile.is_verified
        assert not profile.is_suspended
        profile.full_clean()
        assert Profile.objects.all().count() == 1

    def test_create_profile_with_non_required_fields_successful(self, sample_user):
        """Test creating profiles with non required fields is successful."""
        profile = Profile.objects.create(user=sample_user)

        assert profile.user == sample_user
        assert profile.bio is None
        assert profile.location is None
        assert profile.birth_date is None
        assert profile.website is None
        assert not profile.is_verified
        assert not profile.is_suspended
        profile.full_clean()
        assert Profile.objects.all().count() == 1

    def test_create_profile_without_user_fails(self):
        """Test creating profile without a user fails."""
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                Profile.objects.create()
        assert Profile.objects.all().count() == 0

    def test_minimum_age_validation(self, sample_payload, sample_user):
        """Test validating a profile with age less than 13 raises an error."""
        date_from_12_years_ago = timezone.now().date() - timezone.timedelta(
            days=365 * 12
        )
        sample_payload.update({"birth_date": date_from_12_years_ago})

        profile = Profile.objects.create(**sample_payload, user=sample_user)

        with pytest.raises(ValidationError):
            profile.full_clean()

    def test_website_field_validation(self, sample_payload, sample_user):
        """Test validating profile with invalid url as website raises an error."""
        sample_payload.update({"website": "invalidurl"})

        profile = Profile.objects.create(**sample_payload, user=sample_user)

        with pytest.raises(ValidationError):
            profile.full_clean()

    def test_profile_str(self, sample_user):
        """Test the profile string representation"""
        profile = Profile.objects.create(user=sample_user)

        assert str(profile) == f"{sample_user.first_name} {sample_user.last_name}"

    @patch("uuid.uuid4")
    def test_profile_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = profile_image_file_path(None, "my_image.jpg")

        exp_path = f"uploads/profile/{uuid}.jpg"
        assert file_path == exp_path


@pytest.mark.django_db
class TestFollowModel:
    def test_follow_successful(self):
        """Test create follow each other successful."""
        profile1 = baker.make(Profile)
        profile2 = baker.make(Profile)

        follow = Follow.objects.create(follower=profile1, following=profile2)

        assert follow.follower == profile1
        assert follow.following == profile2
        assert str(follow) == f"{profile1.full_name} follows {profile2.full_name}"
        assert Follow.objects.count() == 1

        follow = Follow.objects.create(follower=profile2, following=profile1)

        assert follow.follower == profile2
        assert follow.following == profile1
        assert str(follow) == f"{profile2.full_name} follows {profile1.full_name}"
        assert Follow.objects.count() == 2

    def test_follow_oneself_fails(self):
        """Test create follow object with same follower and following fails."""
        profile = baker.make(Profile)

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                Follow.objects.create(follower=profile, following=profile)
        assert Follow.objects.count() == 0

    def test_follow_more_than_once_fails(self):
        """Test one profile following another more than once fails."""
        follower = baker.make(Profile)
        following = baker.make(Profile)

        Follow.objects.create(follower=follower, following=following)

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                Follow.objects.create(follower=follower, following=following)
        assert Follow.objects.count() == 1

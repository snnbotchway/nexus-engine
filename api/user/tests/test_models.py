import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

User = get_user_model()


@pytest.fixture
def sample_payload():
    """Return sample user information as a payload."""
    return {
        "username": "sample_username",
        "email": "user@example.com",
        "password": "test_pass_123",
        "first_name": "First name",
        "last_name": "Last name",
    }


@pytest.mark.django_db
class TestUserModel:
    def test_creating_a_user_is_successful(self, sample_payload):
        """Test that users are created successfully."""
        user = User.objects.create_user(**sample_payload)

        assert user.username == sample_payload.get("username")
        assert user.email == sample_payload.get("email")
        assert user.first_name == sample_payload.get("first_name")
        assert user.last_name == sample_payload.get("last_name")
        assert not user.is_staff
        assert not user.is_superuser
        assert user.check_password(sample_payload.get("password"))
        assert User.objects.all().count() == 1

    def test_new_user_email_normalized(self):
        """Test email normalization on user creation."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            user = User.objects.create_user(
                username=expected,
                email=email,
                first_name="Sample first name",
                password="testPass12345",
            )

            assert user.email == expected

    def test_create_user_missing_username_fails(self, sample_payload):
        """Test creating user without username raises an error."""
        sample_payload.update({"username": None})

        with pytest.raises(ValueError) as excinfo:
            User.objects.create_user(**sample_payload)
        assert str(excinfo.value) == "The given username must be set"
        assert User.objects.all().count() == 0

    def test_create_user_missing_email_fails(self, sample_payload):
        """Test creating user without email raises an error."""
        sample_payload.update({"email": None})

        with pytest.raises(ValidationError) as excinfo:
            User.objects.create_user(**sample_payload)
        assert str(excinfo.value.message_dict["email"][0]) == "This field is required."
        assert User.objects.all().count() == 0

    def test_create_user_missing_first_name_fails(self, sample_payload):
        """Test creating user without first name raises an error."""
        sample_payload.update({"first_name": None})

        with pytest.raises(ValidationError) as excinfo:
            User.objects.create_user(**sample_payload)
        assert (
            str(excinfo.value.message_dict["first_name"][0])
            == "This field is required."
        )
        assert User.objects.all().count() == 0

    def test_create_user_with_existing_username_fails(self, sample_payload):
        """Test creating user with existing username raises an error."""
        User.objects.create(**sample_payload)
        sample_payload.update({"email": "different@example.com"})

        # create a new user with the same username
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                User.objects.create(**sample_payload)
        assert User.objects.all().count() == 1

    def test_create_user_with_existing_email_fails(self, sample_payload):
        """Test creating user with existing email raises an error."""
        User.objects.create(**sample_payload)
        sample_payload.update({"username": "other_name"})

        # create a new user with the same email
        with transaction.atomic():
            with pytest.raises(IntegrityError):
                User.objects.create(**sample_payload)
        assert User.objects.all().count() == 1

    def test_create_superuser_successful(self, sample_payload):
        """Test creating a superuser is successful."""
        user = User.objects.create_superuser(**sample_payload)
        assert user.email == sample_payload.get("email")
        assert user.username == sample_payload.get("username")
        assert user.is_staff
        assert user.is_superuser

    def test_create_superuser_missing_is_staff(self, sample_payload):
        """Test creating a superuser with is_staff set to false fails."""
        sample_payload.update({"is_staff": False})

        with pytest.raises(ValueError) as excinfo:
            get_user_model().objects.create_superuser(**sample_payload)
        assert str(excinfo.value) == "Superuser must have is_staff=True."

    def test_create_superuser_missing_is_superuser(self, sample_payload):
        """Test creating a superuser with is_superuser set to false fails."""
        sample_payload.update({"is_superuser": False})
        with pytest.raises(ValueError) as excinfo:
            get_user_model().objects.create_superuser(**sample_payload)
        assert str(excinfo.value) == "Superuser must have is_superuser=True."

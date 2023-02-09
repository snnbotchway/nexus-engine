"""Tests for the User API."""
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from djoser import utils
from djoser.serializers import UserSerializer
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()
REQUIRED_FIELD_ERROR = ["This field may not be blank."]
USER_CREATE_URL = reverse("user:user-list")
USER_ACTIVATION_URL = reverse("user:user-activation")
USER_RESEND_ACTIVATION_URL = reverse("user:user-resend-activation")
USER_URL = reverse("user:user-me")
SET_USERNAME_URL = reverse("user:user-set-username")
RESET_USERNAME_URL = reverse("user:user-reset-username")
RESET_USERNAME_CONFIRM_URL = reverse("user:user-reset-username-confirm")
SET_PASSWORD_URL = reverse("user:user-set-password")
RESET_PASSWORD_URL = reverse("user:user-reset-password")
RESET_PASSWORD_CONFIRM_URL = reverse("user:user-reset-password-confirm")
JWT_CREATE_URL = reverse("user:jwt-create")
JWT_REFRESH_URL = reverse("user:jwt-refresh")
JWT_VERIFY_URL = reverse("user:jwt-verify")


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def sample_user():
    """Create and return a sample user."""
    return User.objects.create_user(
        username="some_user_name",
        email="someemail@example.com",
        password="some password",
        name="some name",
    )


@pytest.fixture
def inactive_user():
    """Create and return an inactive user."""
    return baker.make(User, is_active=False)


@pytest.fixture
def user_payload():
    """Return a payload of sample user information."""
    return {
        "username": "sample_user_name",
        "email": "user@example.com",
        "name": "Sample name",
        "password": "test_pass123",
        "re_password": "test_pass123",
    }


@pytest.fixture
def create_jwt(sample_user, api_client):
    """Create and return token pair for sample_user."""
    payload = {
        "username": sample_user.username,
        "password": "some password",
    }

    response = api_client.post(JWT_CREATE_URL, payload)

    access = response.data.get("access", None)
    refresh = response.data.get("refresh", None)
    return access, refresh, response.status_code


@pytest.mark.django_db
class TestUserCreate:
    def test_create_user_returns_201(self, api_client, user_payload):
        """Test creating a user is successful and email is sent."""

        response = api_client.post(USER_CREATE_URL, user_payload)

        created_user = User.objects.get(username=user_payload.get("username"))
        assert response.status_code == status.HTTP_201_CREATED
        assert created_user.username == user_payload.get("username")
        assert created_user.email == user_payload.get("email")
        assert created_user.name == user_payload.get("name")
        assert not created_user.is_active
        assert created_user.check_password(user_payload.get("password"))
        # Make sure the password is not returned to the user:
        assert "password" not in response.data
        # Assert email was sent to created user:
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [created_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_create_user_if_name_exists_returns_201(
        self, api_client, sample_user, user_payload
    ):
        """Test creating a user with existing name is successful."""
        user_payload.update({"name": sample_user.name})

        response = api_client.post(USER_CREATE_URL, user_payload)

        created_user = User.objects.get(username=user_payload.get("username"))
        assert response.status_code == status.HTTP_201_CREATED
        assert created_user.name == user_payload.get("name")
        assert User.objects.all().count() == 2
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [created_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_create_user_if_username_exists_returns_400(
        self, api_client, sample_user, user_payload
    ):
        """Test create user with a username that already exists returns error."""
        user_payload.update({"username": sample_user.username})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("username") == [
            "A user with that username already exists."
        ]
        assert User.objects.all().count() == 1
        assert len(mail.outbox) == 0

    def test_create_user_if_email_exists_returns_400(
        self, sample_user, api_client, user_payload
    ):
        """Test create user with an email that already exists returns error."""
        user_payload.update({"email": sample_user.email})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("email") == [
            "user with this email address already exists."
        ]
        assert User.objects.all().count() == 1
        assert len(mail.outbox) == 0

    def test_create_user_without_email_returns_400(self, api_client, user_payload):
        """Test create user without an email returns error."""
        user_payload.update({"email": ""})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("email") == REQUIRED_FIELD_ERROR
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_without_username_returns_400(self, api_client, user_payload):
        """Test create user without a username returns error."""
        user_payload.update({"username": ""})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("username") == REQUIRED_FIELD_ERROR
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_without_name_returns_400(self, api_client, user_payload):
        """Test create user without a name returns error."""
        user_payload.update({"name": ""})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("name") == REQUIRED_FIELD_ERROR
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_with_short_password_returns_400(
        self, api_client, user_payload
    ):
        """Test create user with short password returns error."""
        user_payload.update({"password": "wf9283y", "re_password": "wf9283y"})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("password") == [
            "This password is too short. It must contain at least 8 characters."
        ]
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_with_numeric_password_returns_400(
        self, api_client, user_payload
    ):
        """Test create user with numeric password returns error."""
        user_payload.update({"password": "48912734", "re_password": "48912734"})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("password") == ["This password is entirely numeric."]
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_with_common_password_returns_400(
        self, api_client, user_payload
    ):
        """Test create user with common password returns error."""
        user_payload.update({"password": "password", "re_password": "password"})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("password") == ["This password is too common."]
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_with_password_similar_to_email_returns_400(
        self, api_client, user_payload
    ):
        """Test create user with password similar to email returns error."""
        user_payload.update({"password": "@example", "re_password": "@example"})

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("password") == [
            "The password is too similar to the email address."
        ]
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_with_password_similar_to_username_returns_400(
        self, api_client, user_payload
    ):
        """Test create user with password similar to username returns error."""
        user_payload.update(
            {"password": "sampleusername", "re_password": "sampleusername"}
        )

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("password") == [
            "The password is too similar to the username."
        ]
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0

    def test_create_user_if_passwords_dont_match_returns_400(
        self, api_client, user_payload
    ):
        """Test create user with non-matching passwords returns error."""
        user_payload.update(
            {"password": "test_pass123", "re_password": "different_pass123"}
        )

        response = api_client.post(USER_CREATE_URL, user_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("non_field_errors") == [
            "The two password fields didn't match."
        ]
        assert User.objects.all().count() == 0
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestUserActivation:
    def test_activate_user_with_valid_token_returns_204(
        self, api_client, inactive_user
    ):
        """Test that inactive user is activated with valid uid and token."""
        payload = {
            "uid": utils.encode_uid(inactive_user.pk),
            "token": default_token_generator.make_token(inactive_user),
        }

        response = api_client.post(USER_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        inactive_user.refresh_from_db()
        assert inactive_user.is_active
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [inactive_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_user_already_active_returns_403(self, api_client, sample_user):
        """Test that user already active returns error 403."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": default_token_generator.make_token(sample_user),
        }

        response = api_client.post(USER_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data.get("detail") == "Stale token for given user."
        assert len(mail.outbox) == 0

    def test_invalid_uid_returns_400(self, api_client, inactive_user):
        """Test invalid uid returns error."""
        payload = {
            "uid": "invalid_uid",
            "token": default_token_generator.make_token(inactive_user),
        }

        response = api_client.post(USER_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("uid") == ["Invalid user id or user doesn't exist."]
        inactive_user.refresh_from_db()
        assert not inactive_user.is_active
        assert len(mail.outbox) == 0

    def test_invalid_token_returns_400(self, api_client, inactive_user):
        """Test invalid token returns error."""
        payload = {
            "uid": utils.encode_uid(inactive_user.pk),
            "token": "invalid_token",
        }

        response = api_client.post(USER_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("token") == ["Invalid token for given user."]
        inactive_user.refresh_from_db()
        assert not inactive_user.is_active
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestUserResendActivationEmail:
    def test_activation_email_sent(self, api_client, inactive_user):
        """Test that the activation email is sent upon valid request."""
        payload = {"email": inactive_user.email}

        response = api_client.post(USER_RESEND_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [inactive_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_if_user_already_active_returns_400(self, api_client, sample_user):
        """Test that activation email is not sent if the user is already active."""
        payload = {"email": sample_user.email}

        response = api_client.post(USER_RESEND_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(mail.outbox) == 0

    def test_if_email_does_not_exist_returns_400(self, api_client):
        """Test that the activation email is not sent if the email does not exist."""
        payload = {"email": "non_existent@example.com"}

        response = api_client.post(USER_RESEND_ACTIVATION_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestUser:
    def test_get_user_info_returns_200(self, api_client, sample_user):
        """Test retrieve user successful."""
        api_client.force_authenticate(user=sample_user)

        response = api_client.get(USER_URL)

        serializer = UserSerializer(sample_user)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_anonymous_user_get_user_info_returns_401(self, api_client, sample_user):
        """Test anonymous user retrieve user returns error."""
        response = api_client.get(USER_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data.get("detail")
            == "Authentication credentials were not provided."
        )
        serializer = UserSerializer(sample_user)
        assert response.data != serializer.data

    def test_full_update_user(self, api_client, sample_user):
        """Test full update user successful."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "email": "user@example.com",
            "name": "Sample name",
        }

        response = api_client.put(USER_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        sample_user.refresh_from_db()
        serializer = UserSerializer(sample_user)
        assert response.data == serializer.data
        assert sample_user.email == payload.get("email")
        assert sample_user.name == payload.get("name")
        assert not sample_user.is_active
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_partial_update_user(self, api_client, sample_user):
        """Test partial update user successful."""
        api_client.force_authenticate(user=sample_user)
        payload = {"name": "Sample name"}

        response = api_client.patch(USER_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        sample_user.refresh_from_db()
        serializer = UserSerializer(sample_user)
        assert response.data == serializer.data
        assert sample_user.name == payload.get("name")
        assert sample_user.is_active
        # assert len(mail.outbox) == 0 # TODO: Uncomment after djoser update

    def test_update_email_deactivates_user(self, api_client, sample_user):
        """Test user is deactivated and email is sent on email update."""
        api_client.force_authenticate(user=sample_user)
        payload = {"email": "user@example.com"}

        response = api_client.patch(USER_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        sample_user.refresh_from_db()
        serializer = UserSerializer(sample_user)
        assert response.data == serializer.data
        assert sample_user.email == payload.get("email")
        assert not sample_user.is_active
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_update_email_with_same_email_does_not_deactivate(
        self, api_client, sample_user
    ):
        """Test user is not deactivated when email does not change."""
        api_client.force_authenticate(user=sample_user)
        payload = {"email": sample_user.email}

        response = api_client.patch(USER_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        sample_user.refresh_from_db()
        serializer = UserSerializer(sample_user)
        assert response.data == serializer.data
        assert sample_user.email == payload.get("email")
        assert sample_user.is_active
        # assert len(mail.outbox) == 0 # TODO: Uncomment after djoser update

    def test_anonymous_user_full_update_profile_returns_401(
        self, api_client, sample_user
    ):
        """Test anonymous user cannot perform full update."""
        old_email = sample_user.email
        old_name = sample_user.name
        payload = {
            "email": "user@example.com",
            "name": "Sample name",
        }

        response = api_client.put(USER_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data.get("detail")
            == "Authentication credentials were not provided."
        )
        sample_user.refresh_from_db()
        serializer = UserSerializer(sample_user)
        assert response.data != serializer.data
        assert sample_user.email == old_email
        assert sample_user.name == old_name
        assert sample_user.is_active
        assert len(mail.outbox) == 0

    def test_delete_user_returns_204(self, api_client, sample_user):
        """Test delete user successful."""
        api_client.force_authenticate(user=sample_user)
        payload = {"current_password": "some password"}

        response = api_client.delete(USER_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert User.objects.all().count() == 0

    def test_anonymous_user_delete_user_returns_401(self, api_client, sample_user):
        """Test anonymous user cannot perform delete action."""
        payload = {"current_password": "some password"}

        response = api_client.delete(USER_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data.get("detail")
            == "Authentication credentials were not provided."
        )
        assert User.objects.all().count() == 1

    def test_delete_user_with_wrong_password_returns_400(self, api_client, sample_user):
        """Test delete action fails with wrong password."""
        api_client.force_authenticate(user=sample_user)
        payload = {"current_password": "incorrect_password"}

        response = api_client.delete(USER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert User.objects.all().count() == 1


@pytest.mark.django_db
class TestSetUsername:
    def test_set_username_returns_204(self, api_client, sample_user):
        """Test set username is successful."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_username": "new_username",
            "re_new_username": "new_username",
            "current_password": "some password",
        }

        response = api_client.post(SET_USERNAME_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        sample_user.refresh_from_db()
        assert sample_user.username == payload.get("new_username")

    def test_set_username_with_wrong_password_returns_400(
        self, api_client, sample_user
    ):
        """Test set username with wrong password fails."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_username": "new_username",
            "re_new_username": "new_username",
            "current_password": "incorrect password",
        }

        response = api_client.post(SET_USERNAME_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        sample_user.refresh_from_db()
        assert sample_user.username != payload.get("new_username")

    def test_if_usernames_do_not_match_returns_400(self, api_client, sample_user):
        """Test set username with non-matching usernames fails."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_username": "new_username",
            "re_new_username": "different_username",
            "current_password": "some password",
        }

        response = api_client.post(SET_USERNAME_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("non_field_errors") == [
            "The two username fields didn't match."
        ]
        sample_user.refresh_from_db()
        assert sample_user.username != payload.get("new_username")

    def test_anonymous_user_set_username_returns_401(self, api_client, sample_user):
        """Test anonymous user set username fails."""
        payload = {
            "new_username": "new_username",
            "re_new_username": "new_username",
            "current_password": "some password",
        }

        response = api_client.post(SET_USERNAME_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data.get("detail")
            == "Authentication credentials were not provided."
        )
        sample_user.refresh_from_db()
        assert sample_user.username != payload.get("new_username")


@pytest.mark.django_db
class TestResetUsername:
    def test_username_reset_email_sent(self, api_client, sample_user):
        """Test that the username reset email is sent upon valid request."""
        payload = {"email": sample_user.email}

        response = api_client.post(RESET_USERNAME_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_if_email_does_not_exist_returns_204(self, api_client):
        """Test that the username reset email is not sent if email does not exist."""
        payload = {"email": "non_existent@example.com"}

        response = api_client.post(RESET_USERNAME_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestResetUsernameConfirmation:
    def test_reset_username_with_valid_token_returns_204(self, api_client, sample_user):
        """Test that a username is reset with a valid uid and token."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": default_token_generator.make_token(sample_user),
            "new_username": "new_username",
            "re_new_username": "new_username",
        }

        response = api_client.post(RESET_USERNAME_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        sample_user.refresh_from_db()
        assert sample_user.username == payload.get("new_username")
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_invalid_uid_returns_400(self, api_client, sample_user):
        """Test an invalid uid returns error."""
        payload = {
            "uid": "invalid_uid",
            "token": default_token_generator.make_token(sample_user),
            "new_username": "new_username",
            "re_new_username": "new_username",
        }

        response = api_client.post(RESET_USERNAME_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("uid") == ["Invalid user id or user doesn't exist."]
        sample_user.refresh_from_db()
        assert sample_user.username != payload.get("new_username")
        assert len(mail.outbox) == 0

    def test_invalid_token_returns_400(self, api_client, sample_user):
        """Test invalid token returns error."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": "invalid_token",
            "new_username": "new_username",
            "re_new_username": "new_username",
        }

        response = api_client.post(RESET_USERNAME_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("token") == ["Invalid token for given user."]
        sample_user.refresh_from_db()
        assert sample_user.username != payload.get("new_username")
        assert len(mail.outbox) == 0

    def test_non_matching_usernames_returns_400(self, api_client, sample_user):
        """Test reset username with non-matching usernames fails."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": default_token_generator.make_token(sample_user),
            "new_username": "new_username",
            "re_new_username": "different_username",
        }

        response = api_client.post(RESET_USERNAME_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("non_field_errors") == [
            "The two username fields didn't match."
        ]
        sample_user.refresh_from_db()
        assert sample_user.username != payload.get("new_username")
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestSetPassword:
    def test_set_password_returns_204(self, api_client, sample_user):
        """Test set password is successful."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_password": "new_password",
            "re_new_password": "new_password",
            "current_password": "some password",
        }

        response = api_client.post(SET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        sample_user.refresh_from_db()
        assert sample_user.check_password(payload.get("new_password"))

    def test_set_password_with_wrong_password_returns_400(
        self, api_client, sample_user
    ):
        """Test set password with wrong password fails."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_password": "new_password",
            "re_new_password": "new_password",
            "current_password": "incorrect password",
        }

        response = api_client.post(SET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("current_password") == ["Invalid password."]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))

    def test_if_passwords_do_not_match_returns_400(self, api_client, sample_user):
        """Test set password with non-matching passwords fails."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_password": "new_password",
            "re_new_password": "different_password",
            "current_password": "some password",
        }

        response = api_client.post(SET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("non_field_errors") == [
            "The two password fields didn't match."
        ]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))

    def test_weak_password_returns_400(self, api_client, sample_user):
        """Test error is returned upon submitting a weak password."""
        api_client.force_authenticate(user=sample_user)
        payload = {
            "new_password": "1234567",
            "re_new_password": "1234567",
            "current_password": "some password",
        }

        response = api_client.post(SET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # assert 3 password errors; numeric, short and common are returned:
        assert response.data.get("new_password") == [
            "This password is too short. It must contain at least 8 characters.",
            "This password is too common.",
            "This password is entirely numeric.",
        ]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))

    def test_anonymous_user_set_password_returns_401(self, api_client, sample_user):
        """Test anonymous user set password fails."""
        payload = {
            "new_password": "new_password",
            "re_new_password": "new_password",
            "current_password": "some password",
        }

        response = api_client.post(SET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        sample_user.refresh_from_db()
        assert (
            response.data.get("detail")
            == "Authentication credentials were not provided."
        )
        assert not sample_user.check_password(payload.get("new_password"))


@pytest.mark.django_db
class TestResetPassword:
    def test_password_reset_email_sent(self, api_client, sample_user):
        """Test that the password reset email is sent upon valid request."""
        payload = {"email": sample_user.email}

        response = api_client.post(RESET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_if_email_does_not_exist_returns_204(self, api_client):
        """Test that the password reset email is not sent if email does not exist."""
        payload = {"email": "non_existent@example.com"}

        response = api_client.post(RESET_PASSWORD_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestResetPasswordConfirmation:
    def test_reset_password_with_valid_token_returns_204(self, api_client, sample_user):
        """Test that password is reset with valid uid and token."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": default_token_generator.make_token(sample_user),
            "new_password": "new_password",
            "re_new_password": "new_password",
        }

        response = api_client.post(RESET_PASSWORD_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        sample_user.refresh_from_db()
        assert sample_user.check_password(payload.get("new_password"))
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [sample_user.email]
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_invalid_uid_returns_400(self, api_client, sample_user):
        """Test invalid uid returns error."""
        payload = {
            "uid": "invalid_uid",
            "token": default_token_generator.make_token(sample_user),
            "new_password": "new_password",
            "re_new_password": "new_password",
        }

        response = api_client.post(RESET_PASSWORD_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("uid") == ["Invalid user id or user doesn't exist."]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))
        assert len(mail.outbox) == 0

    def test_invalid_token_returns_400(self, api_client, sample_user):
        """Test invalid token returns error."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": "invalid_token",
            "new_password": "new_password",
            "re_new_password": "new_password",
        }

        response = api_client.post(RESET_PASSWORD_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("token") == ["Invalid token for given user."]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))
        assert len(mail.outbox) == 0

    def test_non_matching_passwords_returns_400(self, api_client, sample_user):
        """Test reset password with non-matching passwords fails."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": default_token_generator.make_token(sample_user),
            "new_password": "new_password",
            "re_new_password": "different_password",
        }

        response = api_client.post(RESET_PASSWORD_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("non_field_errors") == [
            "The two password fields didn't match."
        ]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))
        assert len(mail.outbox) == 0

    def test_weak_password_returns_400(self, api_client, sample_user):
        """Test error is returned upon confirmation with weak password."""
        payload = {
            "uid": utils.encode_uid(sample_user.pk),
            "token": default_token_generator.make_token(sample_user),
            "new_password": "1234567",
            "re_new_password": "1234567",
        }

        response = api_client.post(RESET_PASSWORD_CONFIRM_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # assert 3 password errors; numeric, short and common are returned:
        assert response.data.get("new_password") == [
            "This password is too short. It must contain at least 8 characters.",
            "This password is too common.",
            "This password is entirely numeric.",
        ]
        sample_user.refresh_from_db()
        assert not sample_user.check_password(payload.get("new_password"))


@pytest.mark.django_db
class TestJWTCreate:
    def test_create_jwt_returns_200(self, create_jwt):
        """Test creating an access and refresh token is successful."""
        access, refresh, status_code = create_jwt

        assert status_code == status.HTTP_200_OK
        assert access
        assert refresh

    def test_create_jwt__with_invalid_username_returns_401(
        self, api_client, sample_user
    ):
        """Test create jwt with invalid username fails."""
        payload = {
            "username": "non_existing_user",
            "password": "some password",
        }

        response = api_client.post(JWT_CREATE_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data.get("detail")
            == "No active account found with the given credentials"
        )
        assert "access" not in response.data
        assert "refresh" not in response.data

    def test_create_jwt__with_invalid_password_returns_401(
        self, api_client, sample_user
    ):
        """Test create jwt with invalid password fails."""
        payload = {
            "username": sample_user.username,
            "password": "incorrect password",
        }

        response = api_client.post(JWT_CREATE_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data.get("detail")
            == "No active account found with the given credentials"
        )
        assert "access" not in response.data
        assert "refresh" not in response.data

    def test_create_jwt_with_no_password_returns_400(self, api_client, sample_user):
        """Test create jwt without password fails."""
        payload = {
            "username": sample_user.username,
            "password": "",
        }

        response = api_client.post(JWT_CREATE_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("password") == REQUIRED_FIELD_ERROR
        assert "access" not in response.data
        assert "refresh" not in response.data


@pytest.mark.django_db
class TestJWTRefresh:
    def test_refresh_access_token_returns_200(self, api_client, create_jwt):
        """Test refresh access token is successful."""
        access, refresh, status_code = create_jwt
        payload = {"refresh": refresh}

        response = api_client.post(JWT_REFRESH_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "detail" not in response.data
        assert "code" not in response.data

    def test_refresh_access_token_with_invalid_refresh_returns_400(self, api_client):
        """Test refresh access token with invalid refresh token fails."""
        payload = {"refresh": "invalid token"}

        response = api_client.post(JWT_REFRESH_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data.get("detail") == "Token is invalid or expired"
        assert response.data.get("code") == "token_not_valid"
        assert "access" not in response.data

    def test_refresh_access_token_with_no_refresh_returns_400(self, api_client):
        """Test refresh access token without refresh token fails."""
        payload = {"refresh": ""}

        response = api_client.post(JWT_REFRESH_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get("refresh") == REQUIRED_FIELD_ERROR
        assert "access" not in response.data


@pytest.mark.django_db
class TestJWTVerify:
    def test_verify_access_token_returns_200(self, api_client, create_jwt):
        """Test verify access token successful for valid token."""
        access, refresh, status_code = create_jwt
        payload = {"token": access}

        response = api_client.post(JWT_VERIFY_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_verify_refresh_token_returns_200(self, api_client, create_jwt):
        """Test verify refresh token successful for valid token."""
        access, refresh, status_code = create_jwt
        payload = {"token": refresh}

        response = api_client.post(JWT_VERIFY_URL, payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {}

    def test_verify_jwt_with_invalid_token_returns_400(self, api_client):
        """Test verify token  returns error if token is invalid."""
        payload = {"token": "invalid token"}

        response = api_client.post(JWT_VERIFY_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data.get("detail") == "Token is invalid or expired"
        assert response.data.get("code") == "token_not_valid"

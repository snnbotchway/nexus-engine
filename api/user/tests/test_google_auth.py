from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker
from rest_framework.test import APIClient
from social_django.views import get_session_timeout

User = get_user_model()

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
SOCIAL_AUTH_ALLOWED_REDIRECT_URIS = settings.DJOSER["SOCIAL_AUTH_ALLOWED_REDIRECT_URIS"]
GOOGLE_AUTH_URL = "/user/o/google-oauth2/"


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.mark.django_db
class TestGoogleAuth:
    def test_get_authorization_url_returns_200(self, api_client):
        """Test get authorization url is successful."""
        redirect_uri = SOCIAL_AUTH_ALLOWED_REDIRECT_URIS[0]
        url = f"{GOOGLE_AUTH_URL}?redirect_uri={redirect_uri}"

        response = api_client.get(url)

        assert response.status_code == 200
        assert "authorization_url" in response.data

    def test_get_authorization_url_fails_if_redirect_uri_invalid(self, api_client):
        """Test invalid redirect url does not return authorization uri."""
        redirect_uri = "http://invalid-url.com"
        url = f"{GOOGLE_AUTH_URL}?redirect_uri={redirect_uri}"

        response = api_client.get(url)

        assert response.status_code == 400
        assert not response.data

    def test_final_google_authentication_successful(self, api_client, mocker):
        """Test final authentication process is successful."""
        mocker.patch(
            "djoser.social.serializers.ProviderAuthSerializer.validate",
            return_value={"user": baker.make(User)},
        )

        response = api_client.post(f"{GOOGLE_AUTH_URL}?code=code&state=state")

        assert response.status_code == 201
        assert User.objects.all().count() == 1
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data


class TestGetSessionTimeout(TestCase):
    """
    Ensure that the branching logic of get_session_timeout behaves as expected.
    """

    def setUp(self):
        self.social_user = mock.MagicMock()
        self.social_user.expiration_datetime.return_value = None
        super().setUp()

    def set_user_expiration(self, seconds):
        self.social_user.expiration_datetime.return_value = mock.MagicMock(
            total_seconds=mock.MagicMock(return_value=seconds)
        )

    def test_expiration_disabled_no_max(self):
        self.set_user_expiration(60)
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=False
        )
        self.assertIsNone(expiration_length)

    def test_expiration_disabled_with_max(self):
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=False, max_session_length=60
        )
        self.assertEqual(expiration_length, 60)

    def test_expiration_disabled_with_zero_max(self):
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=False, max_session_length=0
        )
        self.assertEqual(expiration_length, 0)

    def test_user_has_session_length_no_max(self):
        self.set_user_expiration(60)
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=True
        )
        self.assertEqual(expiration_length, 60)

    def test_user_has_session_length_larger_max(self):
        self.set_user_expiration(60)
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=True, max_session_length=90
        )
        self.assertEqual(expiration_length, 60)

    def test_user_has_session_length_smaller_max(self):
        self.set_user_expiration(60)
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=True, max_session_length=30
        )
        self.assertEqual(expiration_length, 30)

    def test_user_has_no_session_length_with_max(self):
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=True, max_session_length=60
        )
        self.assertEqual(expiration_length, 60)

    def test_user_has_no_session_length_no_max(self):
        expiration_length = get_session_timeout(
            self.social_user, enable_session_expiration=True
        )
        self.assertIsNone(expiration_length)

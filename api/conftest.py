"""Common test fixtures for this project."""
import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client object."""
    return APIClient()


@pytest.fixture
def sample_user():
    """Create and return a sample user."""
    return baker.make(User)


@pytest.fixture
def not_found_response():
    """Return basic not found response object."""
    return {"detail": "Not found."}


@pytest.fixture
def not_allowed_response():
    """Return the method not allowed error response."""

    def _not_allowed_response(method):
        return {"detail": f'Method "{method}" not allowed.'}

    return _not_allowed_response


@pytest.fixture
def unauthorized_response():
    """Return unauthorized request error response."""
    return {"detail": "Authentication credentials were not provided."}

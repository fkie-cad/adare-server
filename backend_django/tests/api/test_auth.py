import pytest
from django.contrib.auth.models import User

from tests.factories import GiteaUserFactory


DEV_LOGIN_URL = "/api/auth/dev/"
CSRF_URL = "/api/csrf/"
PROTECTED_URL = "/api/run/publish/"  # requires IsAuthenticated


@pytest.mark.django_db
class TestDevLogin:
    def test_dev_login_creates_user_and_token(self, api_client):
        resp = api_client.post(DEV_LOGIN_URL, {"username": "newdevuser"})

        assert resp.status_code == 200
        assert resp.data["user"] == "newdevuser"
        assert "token" in resp.data
        assert "expiry" in resp.data
        assert User.objects.filter(username="newdevuser").exists()

    def test_dev_login_existing_user(self, api_client):
        gitea_user = GiteaUserFactory(user__username="existingdev")

        resp = api_client.post(DEV_LOGIN_URL, {"username": "existingdev"})

        assert resp.status_code == 200
        assert resp.data["user"] == "existingdev"
        assert "token" in resp.data


@pytest.mark.django_db
class TestCSRF:
    def test_csrf_endpoint_sets_cookie(self, api_client):
        resp = api_client.get(CSRF_URL)

        assert resp.status_code == 200


@pytest.mark.django_db
class TestProtectedEndpoints:
    def test_protected_endpoint_without_token(self, api_client):
        resp = api_client.get(PROTECTED_URL)

        assert resp.status_code == 401

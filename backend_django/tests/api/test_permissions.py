import pytest

from experiments.models import generate_ulid
from tests.factories import ExperimentRunFactory, ExperimentFactory, EnvironmentFactory


@pytest.mark.django_db
class TestDeleteRunRequiresAuth:

    def test_unauthenticated_delete_is_rejected(self, api_client):
        run = ExperimentRunFactory()
        response = api_client.delete(f'/api/run/delete/run_{run.ulid}/')
        assert response.status_code in (401, 403)

    def test_authenticated_delete_succeeds(self, authenticated_client):
        run = ExperimentRunFactory()
        response = authenticated_client.delete(f'/api/run/delete/run_{run.ulid}/')
        assert response.status_code == 204


@pytest.mark.django_db
class TestPublishRunRequiresAuth:

    def test_unauthenticated_publish_is_rejected(self, api_client):
        response = api_client.post('/api/run/publish/', {}, format='json')
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestProfileRequiresAuth:

    def test_unauthenticated_profile_is_rejected(self, api_client):
        response = api_client.get('/api/user/profile/')
        assert response.status_code in (401, 403)


@pytest.mark.django_db
class TestPublicProfileView:

    def test_nonexistent_user_returns_404(self, api_client):
        response = api_client.get('/api/user/nonexistent_user_xyz/profile/')
        assert response.status_code == 404


@pytest.mark.django_db
class TestDevLoginRestriction:

    def test_dev_login_available_in_dev_mode(self, api_client):
        """In development mode the endpoint is available and works."""
        response = api_client.post('/api/auth/dev/', {'username': 'devtester'}, format='json')
        assert response.status_code == 200
        assert 'token' in response.data

    def test_dev_login_view_rejects_when_mode_is_production(self, api_client):
        """DevLoginView itself checks MODE and returns 403 in production."""
        from unittest.mock import patch
        with patch('decouple.config', return_value='production'):
            response = api_client.post('/api/auth/dev/', {'username': 'attacker'}, format='json')
            assert response.status_code == 403

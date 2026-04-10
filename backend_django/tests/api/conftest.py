import pytest
from unittest.mock import patch
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    """Disable DRF throttling for all API tests."""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        'DEFAULT_THROTTLE_CLASSES': [],
        'DEFAULT_THROTTLE_RATES': {},
    }


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, gitea_user):
    """Client with Knox token auth."""
    from knox.models import AuthToken
    _, token = AuthToken.objects.create(gitea_user.user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return api_client


@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock Gitea URL converters and MinIO presigned URLs."""
    with patch('helperfunctions.gitea.convert_gitea_internal_api_url_to_viewable_url', side_effect=lambda x: x), \
         patch('helperfunctions.gitea.convert_gitea_internal_api_url_to_external', side_effect=lambda x: x), \
         patch('helperfunctions.minio.get_presigned_url', return_value='http://mock-minio/file'):
        yield


@pytest.fixture
def eager_celery(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

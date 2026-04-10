import pytest

from tests.factories import EnvironmentFactory


ENVIRONMENT_LIST_URL = "/api/environment/"
ENVIRONMENT_FILTER_OPTIONS_URL = "/api/environment/filteroptions/"


def _download_url(name):
    return f"/api/download/environment_{name}/"


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEnvironmentList:
    def test_list_allows_unauthenticated_access(self, api_client):
        resp = api_client.get(ENVIRONMENT_LIST_URL)

        assert resp.status_code == 200

    def test_list_returns_only_published(self, api_client):
        EnvironmentFactory(published=True)
        EnvironmentFactory(published=False, published_at=None)

        resp = api_client.get(ENVIRONMENT_LIST_URL, {"limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1


# ---------------------------------------------------------------------------
# Download view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEnvironmentDownload:
    def test_download_by_name(self, api_client):
        env = EnvironmentFactory(published=True)

        resp = api_client.get(_download_url(env.name))

        assert resp.status_code == 200
        assert resp.data["name"] == env.name
        assert resp.data["ulid"] == env.ulid


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEnvironmentFilterOptions:
    def test_filter_options(self, api_client):
        resp = api_client.get(ENVIRONMENT_FILTER_OPTIONS_URL)

        assert resp.status_code == 200
        assert isinstance(resp.data, dict)

import pytest
from django.contrib.contenttypes.models import ContentType

from experiments.models import Experiment
from tests.factories import (
    ExperimentFactory,
    RequestObjectFactory,
    LabelFactory,
)


REQUEST_LIST_URL = "/api/request/"
REQUEST_FILTER_OPTIONS_URL = "/api/request/filteroptions/"


def _detail_url(ulid):
    return f"/api/request/request_{ulid}/"


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRequestList:
    def test_list_all_requests(self, api_client):
        RequestObjectFactory()
        RequestObjectFactory()

        resp = api_client.get(REQUEST_LIST_URL, {"limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 2


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRequestDetail:
    def test_detail_includes_generic_object(self, api_client):
        exp = ExperimentFactory(published=True)
        ct = ContentType.objects.get_for_model(Experiment)
        req = RequestObjectFactory(objective=ct, object_id=exp.ulid)

        resp = api_client.get(_detail_url(req.ulid))

        assert resp.status_code == 200
        assert resp.data["object"] is not None
        assert resp.data["object"]["ulid"] == exp.ulid


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRequestFilterOptions:
    def test_filter_options_returns_status_and_category(self, api_client):
        label = LabelFactory(name="bugfix")
        RequestObjectFactory(gitea_pr_status="open", labels=[label])

        resp = api_client.get(REQUEST_FILTER_OPTIONS_URL)

        assert resp.status_code == 200
        assert "status" in resp.data
        assert "category" in resp.data
        assert "labels" in resp.data

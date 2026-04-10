import pytest

from tests.factories import (
    TestfunctionSetFactory,
    TestFunctionFactory,
    TestParameterFactory,
)


TESTFUNCTION_LIST_URL = "/api/testfunction/"


def _download_url(name):
    return f"/api/download/testfunction_{name}/"


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTestfunctionList:
    def test_list_returns_published_sets(self, api_client):
        TestfunctionSetFactory(published=True)
        TestfunctionSetFactory(published=False, published_at=None)

        resp = api_client.get(TESTFUNCTION_LIST_URL, {"limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1

    def test_list_includes_nested_functions(self, api_client):
        tfset = TestfunctionSetFactory(published=True)
        param = TestParameterFactory()
        TestFunctionFactory(testfunction_set=tfset, possible_parameters=[param])

        resp = api_client.get(TESTFUNCTION_LIST_URL, {"limit": 100})

        assert resp.status_code == 200
        result = resp.data["results"][0]
        assert len(result["testfunctions"]) == 1
        assert len(result["testfunctions"][0]["possible_parameters"]) == 1

    def test_list_filter_by_name(self, api_client):
        tfset = TestfunctionSetFactory(published=True, name="target-set")
        TestfunctionSetFactory(published=True, name="other-set")

        resp = api_client.get(TESTFUNCTION_LIST_URL, {"name": "target-set", "limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["name"] == tfset.name

    def test_list_search(self, api_client):
        TestfunctionSetFactory(published=True, name="unique-searchable")
        TestfunctionSetFactory(published=True, name="something-else")

        resp = api_client.get(TESTFUNCTION_LIST_URL, {"search": "unique-searchable", "limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["name"] == "unique-searchable"

    def test_list_ordering(self, api_client):
        TestfunctionSetFactory(published=True, name="aaa-set")
        TestfunctionSetFactory(published=True, name="zzz-set")

        resp = api_client.get(TESTFUNCTION_LIST_URL, {"ordering": "name", "limit": 100})

        assert resp.status_code == 200
        names = [r["name"] for r in resp.data["results"]]
        assert names == sorted(names)

        resp = api_client.get(TESTFUNCTION_LIST_URL, {"ordering": "-name", "limit": 100})

        assert resp.status_code == 200
        names = [r["name"] for r in resp.data["results"]]
        assert names == sorted(names, reverse=True)


# ---------------------------------------------------------------------------
# Download view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTestfunctionDownload:
    def test_download_by_name(self, api_client):
        tfset = TestfunctionSetFactory(published=True)

        resp = api_client.get(_download_url(tfset.name))

        assert resp.status_code == 200
        assert resp.data["name"] == tfset.name

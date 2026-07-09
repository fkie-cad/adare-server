import pytest

from tests.factories import (
    ExperimentFactory,
    EnvironmentFactory,
    AbstractTestFactory,
    TagFactory,
    ExperimentRunFactory,
    GiteaUserFactory,
    StatusFactory,
)

EXPERIMENT_LIST_URL = "/api/experiment/"
EXPERIMENT_FILTER_OPTIONS_URL = "/api/experiment/filteroptions/"


def _detail_url(ulid):
    return f"/api/experiment/experiment_{ulid}/"


# ---------------------------------------------------------------------------
# List view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExperimentList:
    def test_list_returns_only_published(self, api_client):
        ExperimentFactory(published=True)
        ExperimentFactory(published=False, published_at=None)

        resp = api_client.get(EXPERIMENT_LIST_URL, {"limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1

    def test_list_pagination(self, api_client):
        ExperimentFactory.create_batch(3)

        resp = api_client.get(EXPERIMENT_LIST_URL, {"limit": 2})

        assert resp.status_code == 200
        assert resp.data["count"] == 3
        assert len(resp.data["results"]) == 2

    def test_list_search_by_name(self, api_client):
        exp = ExperimentFactory(name="unique-search-target")
        ExperimentFactory(name="other-experiment")

        resp = api_client.get(EXPERIMENT_LIST_URL, {"search": exp.name, "limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["ulid"] == exp.ulid

    def test_list_filter_by_tag(self, api_client):
        tag = TagFactory(value="network")
        ExperimentFactory(tags=[tag])
        ExperimentFactory()  # no tag

        resp = api_client.get(EXPERIMENT_LIST_URL, {"tags_mc": "network", "limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1

    def test_list_filter_by_min_runcount(self, api_client):
        exp_with_runs = ExperimentFactory()
        env = EnvironmentFactory()
        exp_with_runs.environments.add(env)
        ExperimentRunFactory(experiment=exp_with_runs, environment=env)
        ExperimentRunFactory(experiment=exp_with_runs, environment=env)

        ExperimentFactory()  # no runs

        resp = api_client.get(EXPERIMENT_LIST_URL, {"min_runcount": 2, "limit": 100})

        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["ulid"] == exp_with_runs.ulid

    def test_list_includes_run_counts(self, api_client):
        exp = ExperimentFactory()
        env = EnvironmentFactory()
        exp.environments.add(env)
        ExperimentRunFactory(
            experiment=exp,
            environment=env,
            result_status=StatusFactory(name="success"),
        )

        resp = api_client.get(EXPERIMENT_LIST_URL, {"limit": 100})

        assert resp.status_code == 200
        result = resp.data["results"][0]
        assert "run_counts" in result
        assert result["run_counts"]["successful"] == 1
        assert result["run_counts"]["failed"] == 0


# ---------------------------------------------------------------------------
# Detail view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExperimentDetail:
    def test_detail_returns_nested_data(self, api_client):
        tag = TagFactory(value="detail-tag")
        env = EnvironmentFactory()
        abstract_test = AbstractTestFactory()
        exp = ExperimentFactory(
            environments=[env],
            abstract_tests=[abstract_test],
            tags=[tag],
        )

        resp = api_client.get(_detail_url(exp.ulid))

        assert resp.status_code == 200
        assert resp.data["ulid"] == exp.ulid
        assert len(resp.data["environments"]) == 1
        assert resp.data["environments"][0]["ulid"] == env.ulid
        assert len(resp.data["abstract_tests"]) == 1
        assert resp.data["abstract_tests"][0]["ulid"] == abstract_test.ulid
        tag_names = [t['name'] for t in resp.data["tags"]]
        assert "detail-tag" in tag_names
        assert "run_counts" in resp.data

    def test_detail_404_for_unpublished(self, api_client):
        exp = ExperimentFactory(published=False, published_at=None)

        resp = api_client.get(_detail_url(exp.ulid))

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExperimentFilterOptions:
    def test_filter_options_returns_tags_and_counts(self, api_client):
        tag = TagFactory(value="filteropts-tag")
        exp = ExperimentFactory(tags=[tag])
        env = EnvironmentFactory()
        exp.environments.add(env)
        ExperimentRunFactory(
            experiment=exp,
            environment=env,
            result_status=StatusFactory(name="success"),
        )

        resp = api_client.get(EXPERIMENT_FILTER_OPTIONS_URL)

        assert resp.status_code == 200
        assert "tags" in resp.data
        tag_names = list(resp.data["tags"])
        assert any("filteropts-tag" in str(t) for t in tag_names)
        assert "max_success" in resp.data
        assert "max_failed" in resp.data
        assert "total_count" in resp.data

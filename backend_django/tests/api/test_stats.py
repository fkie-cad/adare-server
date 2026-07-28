import pytest

from tests.factories import (
    ExperimentFactory,
    EnvironmentFactory,
    ExperimentRunFactory,
    TestfunctionSetFactory,
    TestFunctionFactory,
)


STATS_URL = "/api/stats/"


@pytest.mark.django_db
class TestStatistics:
    def test_returns_all_counts(self, api_client):
        resp = api_client.get(STATS_URL)

        assert resp.status_code == 200
        expected_keys = {
            "experiment_count",
            "run_count",
            "environment_count",
            "testfunctionset_count",
            "testfunction_count",
            "request_count",
            "user_count",
        }
        assert expected_keys == set(resp.data.keys())

    def test_counts_match_database(self, api_client):
        from experiments.models import Experiment, ExperimentRun, Environment, TestfunctionSet, TestFunction

        exp = ExperimentFactory()
        ExperimentFactory()
        env = EnvironmentFactory()
        exp.environments.add(env)
        ExperimentRunFactory(experiment=exp, environment=env)
        tfset = TestfunctionSetFactory()
        TestFunctionFactory(testfunction_set=tfset)
        TestFunctionFactory(testfunction_set=tfset)

        resp = api_client.get(STATS_URL)

        assert resp.status_code == 200
        assert resp.data["experiment_count"] == Experiment.objects.count()
        assert resp.data["run_count"] == ExperimentRun.objects.count()
        assert resp.data["environment_count"] == Environment.objects.count()
        assert resp.data["testfunctionset_count"] == TestfunctionSet.objects.filter(is_current=True).count()
        assert resp.data["testfunction_count"] == TestFunction.objects.count()

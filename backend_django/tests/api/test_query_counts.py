"""Query-count regression tests for the hot list/detail endpoints.

Each test renders the same endpoint against a small and a larger data set and
asserts that the number of SQL queries does not grow with the number of rows
(runs, events, experiments, requests). A failure here means an N+1 crept back
in -- usually a serializer touching a relation the view's queryset does not
select_related/prefetch_related.
"""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext

from tests.factories import (
    AbstractTestFactory,
    ActionEventFactory,
    EnvironmentFactory,
    ErrorEventFactory,
    ExperimentFactory,
    ExperimentRunFactory,
    PostSetupInstallationFactory,
    RequestObjectFactory,
    TagFactory,
    TestEventFactory,
    TestFunctionFactory,
    TestParameterEntryFactory,
    TestParameterFactory,
    TestfunctionSetFactory,
    ToolFactory,
)
from experiments.models import TagScope


def _count_queries(api_client, url, params=None):
    with CaptureQueriesContext(connection) as ctx:
        resp = api_client.get(url, params or {})
    assert resp.status_code == 200, resp.data
    _count_queries.last_sql = [q['sql'] for q in ctx.captured_queries]
    return len(ctx.captured_queries), resp


def _rich_abstract_test():
    """An abstract test touching every relation AbstractTestSerializer renders."""
    testfunction = TestFunctionFactory(
        possible_parameters=[TestParameterFactory(), TestParameterFactory()],
    )
    abstract_test = AbstractTestFactory(
        testfunction=testfunction,
        parameters=[TestParameterEntryFactory(), TestParameterEntryFactory()],
    )
    abstract_test.tools.add(ToolFactory(), ToolFactory())
    return abstract_test


def _scoped_tag():
    scope, _ = TagScope.objects.get_or_create(name='tool')
    return TagFactory(scope=scope)


def _rich_environment():
    return EnvironmentFactory(
        tags=[_scoped_tag(), _scoped_tag()],
        post_setup_installations=[PostSetupInstallationFactory(), PostSetupInstallationFactory()],
    )


def _rich_experiment():
    return ExperimentFactory(
        environments=[_rich_environment(), _rich_environment()],
        abstract_tests=[_rich_abstract_test(), _rich_abstract_test()],
        tags=[_scoped_tag(), _scoped_tag()],
    )


def _run_with_events(experiment, n_events):
    run = ExperimentRunFactory(experiment=experiment)
    abstract_tests = list(experiment.abstract_tests.all())
    # explicit group ids: each event factory has its own Sequence counter, so
    # the defaults collide across types and get collapsed by get_events
    for i in range(n_events):
        TestEventFactory(run=run, abstracttest=abstract_tests[i % len(abstract_tests)],
                         event_group_id=f'test-{i}')
        ActionEventFactory(run=run, event_group_id=f'action-{i}')
        ErrorEventFactory(run=run, event_group_id=f'error-{i}')
    return run


@pytest.mark.django_db
class TestRunQueryCounts:

    def test_run_list_does_not_scale_with_runs_or_events(self, api_client):
        experiment = _rich_experiment()
        _run_with_events(experiment, 1)
        small, _ = _count_queries(api_client, '/api/run/', {'limit': 100})

        for _ in range(5):
            _run_with_events(experiment, 4)
        large, resp = _count_queries(api_client, '/api/run/', {'limit': 100})

        assert resp.data['count'] == 6
        assert large == small, f'run list: {small} queries for 1 run, {large} for 6'
        assert large <= 3

    def test_run_list_omits_events(self, api_client):
        _run_with_events(_rich_experiment(), 2)

        resp = api_client.get('/api/run/', {'limit': 100})

        assert 'events' not in resp.data['results'][0]

    def test_run_detail_does_not_scale_with_events(self, api_client):
        experiment = _rich_experiment()
        run_small = _run_with_events(experiment, 1)
        small, _ = _count_queries(api_client, f'/api/run/run_{run_small.ulid}/')

        run_large = _run_with_events(experiment, 10)
        large, resp = _count_queries(api_client, f'/api/run/run_{run_large.ulid}/')

        assert len(resp.data['events']) == 30
        assert large == small, f'run detail: {small} queries for 3 events, {large} for 30'
        assert large <= 15

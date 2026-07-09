import pytest

from experiments.models import ExperimentRun, Status, ActionEvent, generate_ulid
from tests.factories import (
    ExperimentFactory,
    ExperimentRunFactory,
    EnvironmentFactory,
    ActionEventFactory,
    TestEventFactory,
    ErrorEventFactory,
    GiteaUserFactory,
)


@pytest.mark.django_db
class TestExperimentRunList:

    def test_list_all_runs(self, api_client):
        ExperimentRunFactory()
        ExperimentRunFactory()

        response = api_client.get('/api/run/', {"limit": 100})

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_list_filter_by_ulid(self, api_client):
        run1 = ExperimentRunFactory()
        ExperimentRunFactory()

        # Use a substring of the first run's ulid for filtering
        partial_ulid = run1.ulid[4:12]
        response = api_client.get('/api/run/', {"ulid_contains": partial_ulid, "limit": 100})

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['ulid'] == run1.ulid

    def test_list_pagination(self, api_client):
        ExperimentRunFactory()
        ExperimentRunFactory()
        ExperimentRunFactory()

        response = api_client.get('/api/run/?limit=2')

        assert response.status_code == 200
        assert response.data['count'] == 3
        assert len(response.data['results']) == 2
        assert response.data['next'] is not None


@pytest.mark.django_db
class TestExperimentRunDetail:

    def test_detail_includes_events(self, api_client):
        run = ExperimentRunFactory()
        ActionEventFactory(run=run, event_group_id='1')
        TestEventFactory(run=run, event_group_id='2')

        response = api_client.get(f'/api/run/run_{run.ulid}/')

        assert response.status_code == 200
        assert 'events' in response.data
        assert len(response.data['events']) == 2

        expected_base_fields = {
            'ulid', 'category', 'status', 'success', 'event_group_id',
            'event_type_specific', 'execution_time', 'timestamp',
        }
        for event in response.data['events']:
            assert expected_base_fields.issubset(event.keys()), \
                f"Event {event.get('ulid')} missing: {expected_base_fields - event.keys()}"

    def test_detail_includes_log_urls(self, api_client):
        run = ExperimentRunFactory()

        response = api_client.get(f'/api/run/run_{run.ulid}/')

        assert response.status_code == 200
        # Log files are now optional; just verify they're in the response
        assert 'adarevm_logfile' in response.data


@pytest.mark.django_db
class TestExperimentRunDelete:

    def test_delete_run(self, authenticated_client):
        run = ExperimentRunFactory()
        ActionEventFactory(run=run, event_group_id='1')

        response = authenticated_client.delete(f'/api/run/delete/run_{run.ulid}/')

        assert response.status_code == 204
        assert not ExperimentRun.objects.filter(ulid=run.ulid).exists()

    def test_delete_nonexistent_returns_404(self, authenticated_client):
        fake_ulid = generate_ulid()

        response = authenticated_client.delete(f'/api/run/delete/run_{fake_ulid}/')

        assert response.status_code == 404


@pytest.mark.django_db
class TestExperimentRunCheck:

    def test_check_existing_run(self, api_client):
        run = ExperimentRunFactory()

        response = api_client.get(f'/api/run/check/?ulid={run.ulid}')

        assert response.status_code == 200
        assert response.data['exists'] is True

    def test_check_nonexistent_run(self, api_client):
        response = api_client.get('/api/run/check/?ulid=NONEXISTENT')

        assert response.status_code == 200
        assert response.data['exists'] is False

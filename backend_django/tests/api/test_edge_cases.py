import pytest

from tests.factories import ExperimentRunFactory, ExperimentFactory, EnvironmentFactory


@pytest.mark.django_db
class TestExperimentCheckMultipleView:

    def test_no_body_data_returns_400(self, api_client):
        response = api_client.get('/api/experiment/checkmuliple/')
        assert response.status_code == 400

    def test_empty_hash_string(self, api_client):
        response = api_client.get('/api/experiment/checkmuliple/', data={'sha256hashes': ''}, format='json')
        assert response.status_code == 400

    def test_nonexistent_hashes_returns_empty(self, api_client):
        import json
        # ExperimentCheckMultipleView reads sha256hashes from request.data (body)
        response = api_client.generic(
            'GET',
            '/api/experiment/checkmuliple/',
            data=json.dumps({'sha256hashes': 'deadbeef,cafebabe'}),
            content_type='application/json',
        )
        assert response.status_code == 200
        assert response.data == []


@pytest.mark.django_db
class TestStatisticView:

    def test_empty_database(self, api_client):
        response = api_client.get('/api/stats/')
        assert response.status_code == 200
        assert response.data['experiment_count'] == 0
        assert response.data['run_count'] == 0

    def test_with_data(self, api_client):
        ExperimentRunFactory()
        response = api_client.get('/api/stats/')
        assert response.status_code == 200
        assert response.data['run_count'] >= 1
        assert response.data['experiment_count'] >= 1


@pytest.mark.django_db
class TestFilterOptionsEmpty:

    def test_experiment_filter_options_empty(self, api_client):
        response = api_client.get('/api/experiment/filteroptions/')
        assert response.status_code == 200
        assert 'tags' in response.data

    def test_environment_filter_options_empty(self, api_client):
        response = api_client.get('/api/environment/filteroptions/')
        assert response.status_code == 200
        assert 'tags_by_scope' in response.data

    def test_testfunction_filter_options_empty(self, api_client):
        response = api_client.get('/api/testfunction/filteroptions/')
        assert response.status_code == 200
        assert 'tags_by_scope' in response.data

    def test_request_filter_options_empty(self, api_client):
        response = api_client.get('/api/request/filteroptions/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestExperimentCheckView:

    def test_no_params_returns_400(self, api_client):
        response = api_client.get('/api/experiment/check/')
        assert response.status_code == 400

    def test_nonexistent_ulid(self, api_client):
        response = api_client.get('/api/experiment/check/', {'ulid': 'NONEXISTENT'})
        assert response.status_code == 200
        assert response.data['published'] is None

    def test_nonexistent_hash(self, api_client):
        response = api_client.get('/api/experiment/check/', {'sha256hash': 'deadbeef'})
        assert response.status_code == 200
        assert response.data['published'] is None

    def test_existing_published_experiment(self, api_client):
        exp = ExperimentFactory(published=True)
        response = api_client.get('/api/experiment/check/', {'ulid': exp.ulid})
        assert response.status_code == 200
        assert response.data['published'] is True
        assert response.data['ulid'] == exp.ulid


@pytest.mark.django_db
class TestExperimentDashboard:

    def test_empty_dashboard(self, api_client):
        response = api_client.get('/api/experiment/dashboard/')
        assert response.status_code == 200
        assert response.data['summary']['total_experiments'] == 0
        assert response.data['summary']['total_runs'] == 0

    def test_dashboard_with_runs(self, api_client):
        ExperimentRunFactory()
        response = api_client.get('/api/experiment/dashboard/')
        assert response.status_code == 200
        assert response.data['summary']['total_experiments'] >= 1

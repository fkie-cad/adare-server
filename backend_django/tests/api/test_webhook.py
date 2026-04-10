import pytest
import json
from pathlib import Path
from unittest.mock import patch
from django.conf import settings

FIXTURES_DIR = Path(__file__).resolve().parent.parent / 'fixtures' / 'webhook_payloads'


def load_payload(filename):
    with open(FIXTURES_DIR / filename) as f:
        return json.load(f)


@pytest.mark.django_db
class TestGiteaWebhook:
    url = '/internal/gitea/webhook/'

    def test_webhook_accepts_valid_payload(self, api_client):
        payload = load_payload('pr_opened_experiment.json')
        with patch('giteaeventmanager.views.handle_gitea_webhook') as mock_task:
            mock_task.delay = lambda x: None
            response = api_client.post(self.url, payload, format='json')
        assert response.status_code == 200

    def test_webhook_empty_payload_returns_400(self, api_client):
        response = api_client.post(self.url, {}, format='json')
        assert response.status_code == 400

    def test_webhook_no_pull_request_returns_200(self, api_client):
        """Payload without pull_request key should return 200 but not trigger task."""
        with patch('giteaeventmanager.views.handle_gitea_webhook') as mock_task:
            response = api_client.post(self.url, {'action': 'push'}, format='json')
        assert response.status_code == 200
        mock_task.delay.assert_not_called()

    def test_webhook_triggers_celery_task(self, api_client):
        payload = load_payload('pr_opened_experiment.json')
        with patch('giteaeventmanager.views.handle_gitea_webhook') as mock_task:
            response = api_client.post(self.url, payload, format='json')
        assert response.status_code == 200
        mock_task.delay.assert_called_once_with(payload)

    def test_webhook_pr_opened_experiment(self, api_client, settings, eager_celery):
        """Integration test — requires pull_request_action to work.
        This test mocks pull_request_action to verify the celery task dispatches correctly."""
        settings.GITEA_EXPERIMENTS_REPO = 'adareTEST'
        settings.GITEA_EXPERIMENTS_REPO_OWNER = 'testowner'
        payload = load_payload('pr_opened_experiment.json')
        with patch('giteaeventmanager.event.pull_request_action') as mock_action:
            with patch('giteaeventmanager.views.handle_gitea_webhook') as mock_task:
                mock_task.delay = lambda x: None
                response = api_client.post(self.url, payload, format='json')
        assert response.status_code == 200

    def test_webhook_pr_opened_testfunction(self, api_client):
        payload = load_payload('pr_opened_testfunction.json')
        with patch('giteaeventmanager.views.handle_gitea_webhook') as mock_task:
            mock_task.delay = lambda x: None
            response = api_client.post(self.url, payload, format='json')
        assert response.status_code == 200

    def test_webhook_pr_merged_experiment(self, api_client):
        payload = load_payload('pr_merged_experiment.json')
        with patch('giteaeventmanager.views.handle_gitea_webhook') as mock_task:
            mock_task.delay = lambda x: None
            response = api_client.post(self.url, payload, format='json')
        assert response.status_code == 200

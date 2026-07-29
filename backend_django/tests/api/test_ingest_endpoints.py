"""API tests for the internal ingest/finalize endpoints."""
from pathlib import Path
from unittest.mock import patch

import pytest

from giteaeventmanager.exception import TaskFailure
from experiments.models import Experiment, Request
from tests.factories import (
    EnvironmentFactory,
    GiteaUserFactory,
    TestFunctionFactory,
    TestParameterFactory,
)

INGEST_URL = '/internal/gitea/ingest/'
FINALIZE_URL = '/internal/gitea/finalize/'
SECRET = 'test-webhook-secret'

PLAYBOOK = (
    'name: exp\n'
    'tests:\n'
    '  - name: check-file-exists\n'
    '    description: d\n'
    '    function: is_file\n'
    '    parameter:\n'
    '      path: /tmp/test_file.txt\n'
    'actions:\n'
    '  - test: check-file-exists\n'
)
METADATA = 'environments:\n  - test-env\ntags: []\n'


def _fake_download(url, dest, **kwargs):
    if 'playbook.yml' in url:
        Path(dest).write_text(PLAYBOOK)
        return True
    if 'metadata.yml' in url:
        Path(dest).write_text(METADATA)
        return True
    return False


def _pr(number=1, name='test-experiment', merged=False, state='open'):
    return {
        'number': number,
        'title': f'[experiment create] {name}',
        'body': '',
        'state': state,
        'url': f'http://gitea/api/v1/repos/miq/adareTEST/pulls/{number}',
        'user': {'id': 99999, 'login': 'devuser', 'email': 'devuser@localhost'},
        'head': {'ref': f'submit/experiment/{name}', 'sha': 'deadbeef'},
        'base': {'ref': 'main'},
        'labels': [], 'assignee': None, 'assignees': [], 'requested_reviewers': [],
        'created_at': '2024-01-01T00:00:00+00:00',
        'updated_at': '2024-01-02T00:00:00+00:00',
        'merged': merged,
        'merged_at': '2024-01-03T00:00:00+00:00' if merged else None,
        'merged_by': {'id': 99999, 'login': 'devuser'} if merged else None,
    }


@pytest.fixture(autouse=True)
def _secret(settings):
    settings.GITEA_WEBHOOK_SECRET = SECRET


@pytest.mark.django_db
class TestIngestEndpointAuth:

    def test_missing_secret_returns_400(self, api_client):
        assert api_client.post(f'{INGEST_URL}?prnumber=1').status_code == 400

    def test_wrong_secret_returns_401(self, api_client):
        assert api_client.post(f'{INGEST_URL}?secret=nope&prnumber=1').status_code == 401

    def test_missing_prnumber_returns_400(self, api_client):
        assert api_client.post(f'{INGEST_URL}?secret={SECRET}').status_code == 400

    def test_non_integer_prnumber_returns_400(self, api_client):
        assert api_client.post(f'{INGEST_URL}?secret={SECRET}&prnumber=abc').status_code == 400


@pytest.mark.django_db
class TestIngestEndpoint:

    @pytest.fixture(autouse=True)
    def _fixtures(self, db):
        self.user = GiteaUserFactory()
        EnvironmentFactory(name='test-env')
        TestFunctionFactory(name='standard.is_file')
        TestParameterFactory(name='path')

    def test_ingest_creates_draft_and_returns_result(self, api_client):
        from giteaeventmanager.action.base import PullRequest
        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'), \
             patch.object(PullRequest, '_get_user', return_value=self.user), \
             patch('giteaeventmanager.service._fetch_pull_request', return_value=_pr(number=5)):
            resp = api_client.post(f'{INGEST_URL}?secret={SECRET}&prnumber=5')

        assert resp.status_code == 200
        assert resp.data['experiment_ulid']
        assert [t['name'] for t in resp.data['tests']] == ['check-file-exists']
        exp = Experiment.objects.get(name='test-experiment')
        assert exp.published is False
        assert Request.objects.filter(gitea_pr_number=5).exists()

    def test_ingest_bad_environment_returns_400_with_error(self, api_client):
        from giteaeventmanager.action.base import PullRequest
        bad_metadata = 'environments:\n  - nope-env\ntags: []\n'

        def _dl(url, dest, **kwargs):
            if 'metadata.yml' in url:
                Path(dest).write_text(bad_metadata)
                return True
            return _fake_download(url, dest, **kwargs)

        with patch('giteaeventmanager.action.plugin.download', side_effect=_dl), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'), \
             patch.object(PullRequest, '_get_user', return_value=self.user), \
             patch('giteaeventmanager.service._fetch_pull_request', return_value=_pr(number=6)):
            resp = api_client.post(f'{INGEST_URL}?secret={SECRET}&prnumber=6')

        assert resp.status_code == 400
        assert 'nope-env' in resp.data['error']


@pytest.mark.django_db
class TestFinalizeEndpoint:

    def test_missing_secret_returns_400(self, api_client):
        assert api_client.post(f'{FINALIZE_URL}?prnumber=1').status_code == 400

    def test_finalize_merge_publishes(self, api_client):
        user = GiteaUserFactory()
        EnvironmentFactory(name='test-env')
        TestFunctionFactory(name='standard.is_file')
        TestParameterFactory(name='path')
        from giteaeventmanager.action.base import PullRequest
        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'), \
             patch.object(PullRequest, '_get_user', return_value=user):
            with patch('giteaeventmanager.service._fetch_pull_request', return_value=_pr(number=20)):
                api_client.post(f'{INGEST_URL}?secret={SECRET}&prnumber=20')
            with patch('giteaeventmanager.service._fetch_pull_request',
                       return_value=_pr(number=20, merged=True, state='closed')):
                resp = api_client.post(f'{FINALIZE_URL}?secret={SECRET}&prnumber=20')

        assert resp.status_code == 200
        assert resp.data['published'] is True
        assert Experiment.objects.get(name='test-experiment').published is True

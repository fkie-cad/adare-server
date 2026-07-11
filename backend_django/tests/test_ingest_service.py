"""Unit tests for the synchronous ingest/finalize services."""
from pathlib import Path
from unittest.mock import patch

import pytest

from giteaeventmanager import service
from giteaeventmanager.action.base import PullRequest
from giteaeventmanager.exception import TaskFailure
from experiments.models import Experiment, Request
from tests.factories import (
    EnvironmentFactory,
    GiteaUserFactory,
    TestFunctionFactory,
    TestParameterFactory,
)


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
    """Build a Gitea pull-request object as returned by GET /pulls/{n}."""
    return {
        'number': number,
        'title': f'[experiment create] {name}',
        'body': '',
        'state': state,
        'url': f'http://gitea/api/v1/repos/miq/adareTEST/pulls/{number}',
        'user': {'id': 99999, 'login': 'devuser', 'email': 'devuser@localhost'},
        'head': {'ref': f'submit/experiment/{name}', 'sha': 'deadbeef'},
        'base': {'ref': 'main'},
        'labels': [],
        'assignee': None,
        'assignees': [],
        'requested_reviewers': [],
        'created_at': '2024-01-01T00:00:00+00:00',
        'updated_at': '2024-01-02T00:00:00+00:00',
        'merged': merged,
        'merged_at': '2024-01-03T00:00:00+00:00' if merged else None,
        'merged_by': {'id': 99999, 'login': 'devuser'} if merged else None,
    }


@pytest.fixture
def gitea_env(db):
    """A user, environment and testfunction/parameter matching the sample playbook."""
    user = GiteaUserFactory()
    env = EnvironmentFactory(name='test-env')
    TestFunctionFactory(name='is_file')
    TestParameterFactory(name='path')
    return user, env


@pytest.fixture(autouse=True)
def _mock_gitea(gitea_env):
    """Mock downloads, token retrieval and Gitea user lookups."""
    user = gitea_env[0]
    with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download), \
         patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'), \
         patch.object(PullRequest, '_get_user', return_value=user):
        yield


@pytest.mark.django_db
class TestIngest:

    def test_creates_draft_and_request(self):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=7)):
            result = service.ingest_pr(7)

        exp = Experiment.objects.get(name='test-experiment')
        assert exp.published is False
        req = Request.objects.get(gitea_pr_number=7)
        assert req.object == exp

        assert result['experiment_ulid'] == exp.ulid
        assert result['sha256playbook'] == exp.sha256playbook
        assert [t['name'] for t in result['tests']] == ['check-file-exists']

    def test_reingest_is_idempotent_upsert(self):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=7)):
            service.ingest_pr(7)
            first_ulid = Experiment.objects.get(name='test-experiment').ulid
            service.ingest_pr(7)  # re-run (synchronize)

        assert Request.objects.filter(gitea_pr_number=7).count() == 1
        assert Experiment.objects.filter(name='test-experiment').count() == 1
        # the draft was replaced, not duplicated
        assert Experiment.objects.get(name='test-experiment').ulid != first_ulid

    def test_unknown_environment_raises(self):
        pr = _pr(number=8)
        bad_metadata = 'environments:\n  - does-not-exist\ntags: []\n'

        def _dl(url, dest, **kwargs):
            if 'metadata.yml' in url:
                Path(dest).write_text(bad_metadata)
                return True
            return _fake_download(url, dest, **kwargs)

        with patch('giteaeventmanager.action.plugin.download', side_effect=_dl), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='does-not-exist'):
                service.ingest_pr(8)
        assert not Request.objects.filter(gitea_pr_number=8).exists()

    def test_unknown_testfunction_raises(self):
        from experiments.models import TestFunction
        TestFunction.objects.filter(name='is_file').delete()
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=9)):
            with pytest.raises(TaskFailure, match='is_file'):
                service.ingest_pr(9)


@pytest.mark.django_db
class TestFinalize:

    def _ingest(self, number):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=number)):
            service.ingest_pr(number)

    def test_merge_publishes_and_drops_request(self):
        self._ingest(11)
        with patch.object(service, '_fetch_pull_request',
                          return_value=_pr(number=11, merged=True, state='closed')):
            result = service.finalize_pr(11)

        assert result['merged'] is True and result['published'] is True
        exp = Experiment.objects.get(name='test-experiment')
        assert exp.published is True
        assert exp.published_at is not None
        assert not Request.objects.filter(gitea_pr_number=11).exists()

    def test_close_without_merge_deletes_draft(self):
        self._ingest(12)
        with patch.object(service, '_fetch_pull_request',
                          return_value=_pr(number=12, merged=False, state='closed')):
            result = service.finalize_pr(12)

        assert result['deleted'] is True
        assert not Experiment.objects.filter(name='test-experiment').exists()
        assert not Request.objects.filter(gitea_pr_number=12).exists()

    def test_finalize_without_draft_is_noop(self):
        with patch.object(service, '_fetch_pull_request',
                          return_value=_pr(number=13, merged=False, state='closed')):
            result = service.finalize_pr(13)
        assert result['had_draft'] is False
        assert result['merged'] is False

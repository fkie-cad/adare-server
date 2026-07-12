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
            service.ingest_pr(7)  # re-run (synchronize) with identical content

        assert Request.objects.filter(gitea_pr_number=7).count() == 1
        assert Experiment.objects.filter(name='test-experiment').count() == 1
        # unchanged content -> the draft is preserved, ULID stays stable (no DB churn)
        assert Experiment.objects.get(name='test-experiment').ulid == first_ulid

    def test_reingest_changed_content_replaces_draft(self):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=7)):
            service.ingest_pr(7)
            first = Experiment.objects.get(name='test-experiment')
            first_ulid = first.ulid
            first_hash = first.sha256hash

        # a second ingest whose playbook content differs -> the draft is replaced
        changed_playbook = PLAYBOOK.replace('/tmp/test_file.txt', '/tmp/other_file.txt')

        def _dl(url, dest, **kwargs):
            if 'playbook.yml' in url:
                Path(dest).write_text(changed_playbook)
                return True
            return _fake_download(url, dest, **kwargs)

        with patch('giteaeventmanager.action.plugin.download', side_effect=_dl), \
             patch.object(service, '_fetch_pull_request', return_value=_pr(number=7)):
            service.ingest_pr(7)

        assert Request.objects.filter(gitea_pr_number=7).count() == 1
        assert Experiment.objects.filter(name='test-experiment').count() == 1
        replaced = Experiment.objects.get(name='test-experiment')
        # content changed -> new draft (new ULID, new content hash)
        assert replaced.ulid != first_ulid
        assert replaced.sha256hash != first_hash

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


ENV_VM = (
    'vm: "/media/adare/AdareVMs/Adare-Ubuntu2204.ova"\n'
    'os:\n'
    '  os: Linux\n'
    '  platform: linux\n'
    '  distribution: Ubuntu\n'
    '  version: "22.04"\n'
    'postsetupinstallations:\n'
    '  - name: jinja2\n'
    '    command: pip3 install jinja2\n'
    '    description: templating\n'
    'tags:\n'
    '  - test\n'
)
ENV_VAGRANT = (
    'vagrantbox: generic/ubuntu2204\n'
    'os:\n'
    '  os: Linux\n'
    '  platform: linux\n'
    '  distribution: Ubuntu\n'
    '  version: "22.04"\n'
)
ENV_NO_SOURCE = (
    'os:\n'
    '  os: Linux\n'
    '  platform: linux\n'
    '  distribution: Ubuntu\n'
)
ENV_RECIPE_ONLY = (
    'recipe:\n'
    '  profile: ubuntu-24.04\n'
    '  iso: /isos/ubuntu.iso\n'
    '  iso_sha256: abc123\n'
    'os:\n'
    '  os: Linux\n'
    '  platform: linux\n'
    '  distribution: Ubuntu\n'
)


def _env_pr(number, name, merged=False, state='open'):
    """A Gitea PR whose title routes to the EnvironmentPlugin."""
    pr = _pr(number=number, name=name, merged=merged, state=state)
    pr['title'] = f'[environment create] {name}'
    pr['head']['ref'] = f'submit/environment/{name}'
    return pr


def _env_download(content):
    def _dl(url, dest, **kwargs):
        if 'environments/' in url:
            Path(dest).write_text(content)
            return True
        return False
    return _dl


@pytest.mark.django_db
class TestEnvironmentIngest:
    """Environment PRs route through the EnvironmentPlugin (vm / legacy vagrantbox)."""

    def test_vm_path_creates_environment(self):
        from experiments.models import Environment
        pr = _env_pr(number=20, name='vmenv')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(20)

        env = Environment.objects.get(name='vmenv')
        assert env.vm == '/media/adare/AdareVMs/Adare-Ubuntu2204.ova'
        assert env.vagrantbox == ''
        assert env.os_info.platform == 'linux'
        # postsetupinstallations must ingest without error (regression: tuple bug)
        assert env.post_setup_installations.count() == 1
        assert env.post_setup_installations.first().name == 'jinja2'

    def test_legacy_vagrantbox_path_creates_environment(self):
        from experiments.models import Environment
        pr = _env_pr(number=21, name='boxenv')

        class _Resp:
            status_code = 200

        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VAGRANT)), \
             patch('giteaeventmanager.action.plugin.requests.get', return_value=_Resp()), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(21)

        env = Environment.objects.get(name='boxenv')
        assert env.vagrantbox == 'generic/ubuntu2204'
        assert env.vm == ''

    def test_missing_source_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=22, name='badenv')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_NO_SOURCE)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='VM source'):
                service.ingest_pr(22)
        assert not Environment.objects.filter(name='badenv').exists()

    def test_recipe_only_raises_taskfailure(self):
        from experiments.models import Environment
        pr = _env_pr(number=23, name='recipeenv')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_RECIPE_ONLY)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='recipe'):
                service.ingest_pr(23)
        assert not Environment.objects.filter(name='recipeenv').exists()


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

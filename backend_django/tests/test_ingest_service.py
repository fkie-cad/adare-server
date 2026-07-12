"""Unit tests for the synchronous ingest/finalize services."""
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

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


ENV_VM_SHA256 = 'c' * 64
# A `vm` submitted to the server must be a published http(s) URL (a bare local
# path is reference-only and not publishable, per CONTRACT.md); the server
# HEAD-checks reachability at create time, so callers must mock
# `plugin.requests.head` (see `_ok_head_patch` below).
ENV_VM = (
    'vm: "https://host.example/Adare-Ubuntu2204.ova"\n'
    f'vm_sha256: {ENV_VM_SHA256}\n'
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
RECIPE_ISO_SHA256 = 'a' * 64
ENV_RECIPE_ONLY = (
    'recipe:\n'
    '  profile: ubuntu-24.04\n'
    '  iso: /isos/ubuntu.iso\n'
    f'  iso_sha256: {RECIPE_ISO_SHA256}\n'
    '  template: ""\n'
    '  params:\n'
    '    setup_level: 1\n'
    '    disk_size: 40G\n'
    '    ram_mb: 4096\n'
    '    cpus: 2\n'
    '    arch: x86_64\n'
    'os:\n'
    '  os: Ubuntu 24.04\n'
    '  platform: linux\n'
    '  distribution: Ubuntu\n'
    '  version: "24.04"\n'
)
BAKED_VM_SHA256 = 'b' * 64
ENV_BAKED_URL = (
    'vm: "https://host.example/foo.ova"\n'
    f'vm_sha256: {BAKED_VM_SHA256}\n'
    'os:\n'
    '  os: Linux\n'
    '  platform: linux\n'
    '  distribution: Ubuntu\n'
    '  version: "22.04"\n'
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


class _OkResp:
    """A reachable-URL stand-in for `requests.get`/`.head` (status 200)."""
    status_code = 200


@pytest.mark.django_db
class TestEnvironmentIngest:
    """Environment PRs route through the EnvironmentPlugin (vm / legacy vagrantbox)."""

    def test_vm_path_creates_environment(self):
        from experiments.models import Environment
        pr = _env_pr(number=20, name='vmenv')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(20)

        env = Environment.objects.get(name='vmenv')
        assert env.vm == 'https://host.example/Adare-Ubuntu2204.ova'
        assert env.vm_sha256 == ENV_VM_SHA256
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

    def test_recipe_creates_environment(self):
        from experiments.models import Environment
        pr = _env_pr(number=23, name='recipeenv')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_RECIPE_ONLY)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(23)

        env = Environment.objects.get(name='recipeenv')
        assert env.vm == ''
        assert env.vagrantbox == ''
        assert env.recipe is not None
        assert env.recipe.profile == 'ubuntu-24.04'
        assert env.recipe.iso == '/isos/ubuntu.iso'
        assert env.recipe.iso_sha256 == RECIPE_ISO_SHA256
        assert env.recipe.setup_level == 1
        assert env.recipe.disk_size == '40G'
        assert env.recipe.ram_mb == 4096
        assert env.recipe.cpus == 2
        assert env.recipe.arch == 'x86_64'

    def test_recipe_missing_iso_sha256_raises_taskfailure(self):
        from experiments.models import Environment
        pr = _env_pr(number=24, name='recipe-badenv')
        bad_recipe = (
            'recipe:\n'
            '  profile: ubuntu-24.04\n'
            '  iso: /isos/ubuntu.iso\n'
            'os:\n'
            '  os: Linux\n'
            '  platform: linux\n'
            '  distribution: Ubuntu\n'
        )
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(bad_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='iso_sha256'):
                service.ingest_pr(24)
        assert not Environment.objects.filter(name='recipe-badenv').exists()

    def test_recipe_non_hex_iso_sha256_raises_taskfailure(self):
        from experiments.models import Environment
        pr = _env_pr(number=25, name='recipe-badhash')
        bad_recipe = ENV_RECIPE_ONLY.replace(RECIPE_ISO_SHA256, 'not-a-valid-hash')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(bad_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='iso_sha256'):
                service.ingest_pr(25)
        assert not Environment.objects.filter(name='recipe-badhash').exists()

    def test_baked_url_creates_environment(self):
        from experiments.models import Environment
        pr = _env_pr(number=26, name='bakedenv')

        class _Resp:
            status_code = 200

        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_BAKED_URL)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_Resp()), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(26)

        env = Environment.objects.get(name='bakedenv')
        assert env.vm == 'https://host.example/foo.ova'
        assert env.vm_sha256 == BAKED_VM_SHA256

    def test_baked_local_path_rejected(self):
        from experiments.models import Environment
        pr = _env_pr(number=27, name='baked-localpath')
        local_path_env = ENV_BAKED_URL.replace('https://host.example/foo.ova', '/media/adare/AdareVMs/foo.ova')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(local_path_env)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='http'):
                service.ingest_pr(27)
        assert not Environment.objects.filter(name='baked-localpath').exists()

    def test_baked_malformed_sha256_rejected(self):
        from experiments.models import Environment
        pr = _env_pr(number=28, name='baked-badhash')
        bad_env = ENV_BAKED_URL.replace(BAKED_VM_SHA256, 'not-a-valid-hash')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(bad_env)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='vm_sha256'):
                service.ingest_pr(28)
        assert not Environment.objects.filter(name='baked-badhash').exists()

    def test_baked_unreachable_url_raises_via_exception(self):
        from experiments.models import Environment
        pr = _env_pr(number=29, name='baked-unreachable')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_BAKED_URL)), \
             patch('giteaeventmanager.action.plugin.requests.head',
                   side_effect=requests.RequestException('boom')), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='could not reach'):
                service.ingest_pr(29)
        assert not Environment.objects.filter(name='baked-unreachable').exists()

    def test_baked_unreachable_url_raises_via_status(self):
        from experiments.models import Environment
        pr = _env_pr(number=30, name='baked-404')

        class _Resp:
            status_code = 404

        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_BAKED_URL)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_Resp()), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='unreachable'):
                service.ingest_pr(30)
        assert not Environment.objects.filter(name='baked-404').exists()

    # -- regression: author-controlled YAML scalars must never reach urlparse()/
    #    re.match() unguarded (those raise AttributeError/TypeError -> 500, not
    #    a clean TaskFailure/400). --

    def test_numeric_vm_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=31, name='baked-numeric-vm')
        numeric_vm_env = (
            'vm: 12345\n'
            'os:\n'
            '  os: Linux\n'
            '  platform: linux\n'
            '  distribution: Ubuntu\n'
        )
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(numeric_vm_env)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='vm'):
                service.ingest_pr(31)
        assert not Environment.objects.filter(name='baked-numeric-vm').exists()

    def test_numeric_vm_sha256_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=32, name='baked-numeric-hash')
        # an unquoted all-digit 64-char scalar parses as a YAML int, not a str
        numeric_hash_env = ENV_BAKED_URL.replace(BAKED_VM_SHA256, '1' * 64)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(numeric_hash_env)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='vm_sha256'):
                service.ingest_pr(32)
        assert not Environment.objects.filter(name='baked-numeric-hash').exists()

    def test_numeric_recipe_iso_sha256_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=33, name='recipe-numeric-hash')
        numeric_hash_recipe = ENV_RECIPE_ONLY.replace(RECIPE_ISO_SHA256, '1' * 64)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(numeric_hash_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='iso_sha256'):
                service.ingest_pr(33)
        assert not Environment.objects.filter(name='recipe-numeric-hash').exists()

    def test_recipe_non_int_setup_level_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=34, name='recipe-bad-setup-level')
        bad_params_recipe = ENV_RECIPE_ONLY.replace('setup_level: 1\n', 'setup_level: "one"\n')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(bad_params_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='setup_level'):
                service.ingest_pr(34)
        assert not Environment.objects.filter(name='recipe-bad-setup-level').exists()

    # -- regression: author-controlled fields must be length-checked against
    #    the Recipe/Environment CharField columns before any DB write, since
    #    Recipe.objects.create()/Environment.save() skip full_clean() and an
    #    over-long value would otherwise only fail as a raw Postgres DataError
    #    (a 500), not TaskFailure. --

    def test_recipe_iso_too_long_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=35, name='recipe-long-iso')
        long_iso_recipe = ENV_RECIPE_ONLY.replace('/isos/ubuntu.iso', '/isos/' + 'a' * 2000 + '.iso')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(long_iso_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='iso'):
                service.ingest_pr(35)
        assert not Environment.objects.filter(name='recipe-long-iso').exists()

    def test_recipe_profile_too_long_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=36, name='recipe-long-profile')
        long_profile_recipe = ENV_RECIPE_ONLY.replace('ubuntu-24.04', 'a' * 201, 1)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(long_profile_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='profile'):
                service.ingest_pr(36)
        assert not Environment.objects.filter(name='recipe-long-profile').exists()

    def test_vm_url_too_long_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=37, name='baked-long-vm')
        long_vm = 'https://host.example/' + ('a' * 2000) + '.ova'
        long_vm_env = ENV_BAKED_URL.replace('https://host.example/foo.ova', long_vm)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(long_vm_env)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='vm'):
                service.ingest_pr(37)
        assert not Environment.objects.filter(name='baked-long-vm').exists()

    def test_empty_yaml_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=38, name='empty-yaml-env')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download('')), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='mapping'):
                service.ingest_pr(38)
        assert not Environment.objects.filter(name='empty-yaml-env').exists()

    def test_non_dict_yaml_raises_taskfailure_not_500(self):
        from experiments.models import Environment
        pr = _env_pr(number=39, name='list-yaml-env')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download('[]\n')), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure, match='mapping'):
                service.ingest_pr(39)
        assert not Environment.objects.filter(name='list-yaml-env').exists()


@pytest.mark.django_db
class TestNameCollisionSafetyNet:
    """Server-side read-only reconciliation when a create PR collides by name.

    The client normally reuses an open PR (so re-ingest hits the same-PR upsert),
    but a stray duplicate PR can still reach the server. These cases exercise the
    name-collision branch without any write back to Gitea.
    """

    def _ingest_env(self, number, name):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(number, name)):
            service.ingest_pr(number)

    def test_stale_draft_reconciled(self):
        """A draft left by a closed/merged PR is reconciled; the new PR ingests 200."""
        from experiments.models import Environment
        self._ingest_env(40, 'stale-env')
        assert Request.objects.filter(gitea_pr_number=40).exists()

        # PR 40 is now closed (finalize never ran -> the draft leaked). Re-upload as PR 41.
        def _fetch(number):
            if number == 40:
                return _env_pr(40, 'stale-env', state='closed')
            return _env_pr(41, 'stale-env', state='open')

        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', side_effect=_fetch):
            service.ingest_pr(41)

        assert not Request.objects.filter(gitea_pr_number=40).exists()
        assert Request.objects.filter(gitea_pr_number=41).exists()
        assert Environment.objects.filter(name='stale-env').count() == 1

    def test_open_pr_duplicate_rejected(self):
        """A second, still-open PR for the same name is rejected with the #M hint."""
        from experiments.models import Environment
        self._ingest_env(50, 'dup-env')

        def _fetch(number):
            if number == 50:
                return _env_pr(50, 'dup-env', state='open')
            return _env_pr(51, 'dup-env', state='open')

        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch.object(service, '_fetch_pull_request', side_effect=_fetch):
            with pytest.raises(TaskFailure, match='#50'):
                service.ingest_pr(51)

        assert not Request.objects.filter(gitea_pr_number=51).exists()
        assert Request.objects.filter(gitea_pr_number=50).exists()
        assert Environment.objects.filter(name='dup-env').count() == 1

    def test_published_name_collision_rejected(self):
        """Colliding with an already-published object points at the modify path."""
        from experiments.models import Environment
        self._ingest_env(60, 'pub-env')
        env = Environment.objects.get(name='pub-env')
        env.published = True
        env.save()

        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(61, 'pub-env')):
            with pytest.raises(TaskFailure, match='already published'):
                service.ingest_pr(61)

        assert not Request.objects.filter(gitea_pr_number=61).exists()


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

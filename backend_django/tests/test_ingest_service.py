"""Unit tests for the synchronous ingest/finalize services."""
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from giteaeventmanager import service
from giteaeventmanager.action.base import PullRequest
from giteaeventmanager.errorcodes import SubmitErrorCode
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
    """A user, environment and testfunction/parameter matching the sample playbook.

    The playbook's `function: is_file` is unprefixed, which resolves against the
    `standard` set, so the stored name is the qualified `standard.is_file`
    (see plugin.qualify_test_name / qualify_playbook_function).
    """
    user = GiteaUserFactory()
    env = EnvironmentFactory(name='test-env')
    TestFunctionFactory(name='standard.is_file')
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
        TestFunction.objects.filter(name='standard.is_file').delete()
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=9)):
            with pytest.raises(TaskFailure, match='is_file'):
                service.ingest_pr(9)


ENV_VM_SHA256 = 'c' * 64
# A `vm` submitted to the server must be a published http(s) URL (a bare local
# path is reference-only and not publishable); the server HEAD-checks
# reachability at create time, so callers must mock `plugin.requests.head`
# (see `_OkResp` below).
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
# A hosted recipe ISO must be an http(s) URL, same rule as the baked `vm` source:
# a bare local path (`/isos/ubuntu.iso`) resolves only on the publisher's own
# machine. The Windows-only BYO form (`iso_name`, see ENV_RECIPE_BYO) is the one
# way to publish a recipe without hosting the ISO.
RECIPE_ISO_URL = 'https://mirror.example/ubuntu-24.04.iso'
ENV_RECIPE_ONLY = (
    'recipe:\n'
    '  profile: ubuntu-24.04\n'
    f'  iso: "{RECIPE_ISO_URL}"\n'
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
# BYO ('bring your own') ISO: Windows only, because a Microsoft Windows ISO may
# not legally be rehosted. `iso_name` is a bare filename the consumer supplies
# locally and `iso_sha256` stays the integrity boundary.
BYO_ISO_SHA256 = 'd' * 64
BYO_ISO_NAME = 'Win11_25H2_English_Arm64_v2.iso'
# publisher-supplied plain text; never rendered as markdown/HTML by a frontend
BYO_ISO_NOTES_YAML = (
    '  iso_notes: |\n'
    '    Download from https://www.microsoft.com/software-download/windows11\n'
    '    "Windows 11 Arm64", English (International). Requires a valid licence.\n'
)
ENV_RECIPE_BYO = (
    'recipe:\n'
    '  profile: windows11arm64\n'
    f'  iso_name: {BYO_ISO_NAME}\n'
    f'  iso_sha256: {BYO_ISO_SHA256}\n'
    f'{BYO_ISO_NOTES_YAML}'
    '  template: autounattend_win11_arm64.xml\n'
    '  params:\n'
    '    setup_level: 2\n'
    '    disk_size: 160G\n'
    '    ram_mb: 8192\n'
    '    cpus: 4\n'
    'os:\n'
    '  os: Windows 11\n'
    '  platform: windows\n'
    '  distribution: Windows\n'
    '  version: "11"\n'
)
# A provision block covering both entry shapes: a single command and a
# `for_each` group whose steps carry the optional fields.
PROVISION_YAML = (
    '  provision:\n'
    '    - name: boot-hardening\n'
    '      description: Survive a hard power-off without Startup Repair\n'
    '      shell: cmd\n'
    "      command: 'bcdedit /set {default} bootstatuspolicy ignoreallfailures'\n"
    '    - name: autopsy\n'
    '      description: Autopsy {{ item }}\n'
    '      for_each: ["4.4.0", "4.4.1"]\n'
    '      steps:\n'
    '        - name: autopsy-{{ item }}-download\n'
    "          command: 'curl.exe -L -f -o \"$env:TEMP\\autopsy.msi\" https://host.example/a.msi'\n"
    '          timeout_minutes: 20\n'
    '        - name: autopsy-{{ item }}-install\n'
    "          command: 'msiexec /i \"$env:TEMP\\autopsy.msi\" /qn'\n"
    '          allow_exit_codes: [0, 3010]\n'
    "          verify: 'if (-not (Test-Path \"C:\\Program Files\\Autopsy\")) { exit 1 }'\n"
    "          log_files: ['C:\\Temp\\autopsy-msi.log']\n"
    '          timeout_minutes: 45\n'
    '          reboot: false\n'
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


def _recipe_with_provision(base, provision_yaml=PROVISION_YAML):
    """Insert a `provision:` block at the end of `base`'s recipe block."""
    return base.replace('\nos:\n', '\n' + provision_yaml + 'os:\n', 1)


def _expect_invalid_content(number, name, content, match):
    """Ingest `content` as an environment and assert it is rejected, cleanly.

    A rejected environment must raise TaskFailure(INVALID_CONTENT) -- never an
    AttributeError/TypeError/DataError bubbling up as a 500 -- and must leave no
    partially written row behind.
    """
    from experiments.models import Environment
    with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(content)), \
         patch.object(service, '_fetch_pull_request', return_value=_env_pr(number, name)):
        with pytest.raises(TaskFailure, match=match) as exc:
            service.ingest_pr(number)
    assert exc.value.code == SubmitErrorCode.INVALID_CONTENT
    assert not Environment.objects.filter(name=name).exists()


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
        assert env.recipe.iso == RECIPE_ISO_URL
        assert env.recipe.iso_name == ''
        assert env.recipe.iso_notes == ''
        assert env.recipe.provision == []
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
            f'  iso: "{RECIPE_ISO_URL}"\n'
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
        long_iso_recipe = ENV_RECIPE_ONLY.replace(
            RECIPE_ISO_URL, 'https://mirror.example/' + 'a' * 2000 + '.iso')
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
class TestRecipeIsoContract:
    """The two recipe ISO forms: a hosted http(s) `iso`, or a Windows-only BYO `iso_name`.

    Exactly one must be present. These checks live in
    `giteaeventmanager.action.environment_contract.check_recipe_block`, which is a
    coarse filter only: it trusts `os.platform`, because the server has no
    OS-profile catalog to resolve `recipe.profile` against. The authoritative
    profile->platform gate is consumer-side in the client.
    """

    def test_recipe_local_iso_path_rejected(self):
        # a bare local path resolves only on the publisher's machine; same rule
        # the baked `vm` source has always applied
        local_iso = ENV_RECIPE_ONLY.replace(RECIPE_ISO_URL, '/isos/ubuntu.iso')
        _expect_invalid_content(130, 'recipe-local-iso', local_iso, 'http')

    def test_recipe_non_http_scheme_iso_rejected(self):
        ftp_iso = ENV_RECIPE_ONLY.replace(RECIPE_ISO_URL, 'ftp://mirror.example/ubuntu.iso')
        _expect_invalid_content(131, 'recipe-ftp-iso', ftp_iso, 'http')

    def test_byo_iso_creates_environment(self):
        from experiments.models import Environment
        pr = _env_pr(number=132, name='byoenv')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_RECIPE_BYO)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(132)

        env = Environment.objects.get(name='byoenv')
        assert env.vm == ''
        assert env.vagrantbox == ''
        assert env.recipe is not None
        assert env.recipe.profile == 'windows11arm64'
        # no URL to download: the consumer supplies the file, the digest binds it
        assert env.recipe.iso == ''
        assert env.recipe.iso_name == BYO_ISO_NAME
        assert env.recipe.iso_sha256 == BYO_ISO_SHA256
        assert env.recipe.iso_notes.startswith('Download from https://')
        assert env.recipe.template == 'autounattend_win11_arm64.xml'
        assert env.recipe.setup_level == 2
        assert env.recipe.ram_mb == 8192

    def test_byo_iso_round_trips_through_serializer(self):
        from experiments.models import Environment
        from experiments.serializers import RecipeSerializer
        pr = _env_pr(number=133, name='byoenv-api')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_RECIPE_BYO)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(133)

        # the API must describe the BYO form truthfully, or a consumer sees an
        # environment with no ISO at all
        data = RecipeSerializer(Environment.objects.get(name='byoenv-api').recipe).data
        assert data['iso'] == ''
        assert data['iso_name'] == BYO_ISO_NAME
        assert data['iso_sha256'] == BYO_ISO_SHA256
        assert 'microsoft.com' in data['iso_notes']

    def test_byo_iso_rejected_for_non_windows_platform(self):
        linux_byo = ENV_RECIPE_BYO.replace('  platform: windows\n', '  platform: linux\n')
        _expect_invalid_content(134, 'byo-linux', linux_byo, 'only allowed for Windows')

    @pytest.mark.parametrize('bad_name', [
        '../../etc/passwd',
        '../win.iso',
        'sub/dir/w.iso',
        '/abs/path/w.iso',
        'C:\\ISOs\\w.iso',
        'https://host.example/w.iso',
        '-rf.iso',
    ])
    def test_byo_iso_name_with_path_rejected(self, bad_name):
        # ISO_NAME_RE admits a bare filename only: no separators, no '..', no
        # scheme, no drive letter, and no leading '-' (never mistakable for a flag)
        content = ENV_RECIPE_BYO.replace(BYO_ISO_NAME, bad_name)
        name = f'byo-path-{abs(hash(bad_name)) % 10000}'
        _expect_invalid_content(135, name, content, 'iso_name')

    def test_byo_iso_name_padding_stripped(self):
        # the client validates iso_name.strip(), so a padded quoted scalar
        # publishes fine; the server must accept it and store the canonical form
        from experiments.models import Environment
        content = ENV_RECIPE_BYO.replace(
            f'  iso_name: {BYO_ISO_NAME}\n', f'  iso_name: "  {BYO_ISO_NAME}  "\n')
        pr = _env_pr(number=143, name='byo-padded-name')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(content)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(143)

        assert Environment.objects.get(name='byo-padded-name').recipe.iso_name == BYO_ISO_NAME

    def test_byo_iso_name_wrong_extension_rejected(self):
        content = ENV_RECIPE_BYO.replace(BYO_ISO_NAME, 'Win11_25H2.img')
        _expect_invalid_content(136, 'byo-bad-ext', content, 'iso_name')

    def test_byo_iso_name_numeric_rejected(self):
        # an unquoted numeric scalar parses as an int; it must not reach re.match()
        content = ENV_RECIPE_BYO.replace(f'iso_name: {BYO_ISO_NAME}', 'iso_name: 12345')
        _expect_invalid_content(137, 'byo-numeric-name', content, 'iso_name')

    def test_byo_iso_name_too_long_rejected(self):
        content = ENV_RECIPE_BYO.replace(BYO_ISO_NAME, 'a' * 250 + '.iso')
        _expect_invalid_content(138, 'byo-long-name', content, 'iso_name')

    def test_both_iso_and_iso_name_rejected(self):
        content = ENV_RECIPE_BYO.replace(
            f'  iso_name: {BYO_ISO_NAME}\n',
            f'  iso_name: {BYO_ISO_NAME}\n  iso: "{RECIPE_ISO_URL}"\n')
        _expect_invalid_content(139, 'byo-both', content, 'exactly one ISO source')

    def test_neither_iso_nor_iso_name_rejected(self):
        # a typo'd key ('iso_nmae') is silently dropped by the client's cattrs
        # structuring, so "no ISO at all" has to be an explicit rejection
        content = ENV_RECIPE_BYO.replace('  iso_name: ', '  iso_nmae: ')
        _expect_invalid_content(140, 'byo-neither', content, 'missing its ISO source')

    def test_uppercase_iso_sha256_rejected(self):
        # the consumer's verify_iso_hash compares case-sensitively, so an
        # uppercase digest would publish fine and never build
        content = ENV_RECIPE_ONLY.replace(RECIPE_ISO_SHA256, 'A' * 64)
        _expect_invalid_content(141, 'recipe-upper-hash', content, 'iso_sha256')

    def test_iso_notes_too_long_rejected(self):
        content = ENV_RECIPE_BYO.replace(
            BYO_ISO_NOTES_YAML, f'  iso_notes: "{"n" * 1001}"\n')
        _expect_invalid_content(142, 'byo-long-notes', content, 'iso_notes')


@pytest.mark.django_db
class TestRecipeProvision:
    """`recipe.provision`: build-time steps, stored verbatim, run once per disk build.

    Distinct from `postsetupinstallations`, which run again on every experiment run.
    """

    def test_provision_ingests_and_round_trips(self):
        from experiments.models import Environment
        from experiments.serializers import RecipeSerializer
        pr = _env_pr(number=150, name='provenv')
        content = _recipe_with_provision(ENV_RECIPE_BYO)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(content)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(150)

        recipe = Environment.objects.get(name='provenv').recipe
        # stored as declared: the `for_each` group is NOT expanded server-side
        assert [entry['name'] for entry in recipe.provision] == ['boot-hardening', 'autopsy']
        command_entry, group_entry = recipe.provision
        assert command_entry['shell'] == 'cmd'
        assert command_entry['command'].startswith('bcdedit /set {default}')
        assert group_entry['for_each'] == ['4.4.0', '4.4.1']
        assert [step['name'] for step in group_entry['steps']] == [
            'autopsy-{{ item }}-download', 'autopsy-{{ item }}-install']
        install_step = group_entry['steps'][1]
        assert install_step['allow_exit_codes'] == [0, 3010]
        assert install_step['timeout_minutes'] == 45
        assert install_step['reboot'] is False
        assert install_step['log_files'] == ['C:\\Temp\\autopsy-msi.log']

        # the API must say the environment is provisioned, not a bare OS install
        assert RecipeSerializer(recipe).data['provision'] == recipe.provision

    def test_provision_group_accepts_inherited_leaf_keys(self):
        # the client's ProvisionStep subclasses ProvisionCommand, so a group entry
        # may legally carry leaf keys (inert, but accepted at publish time) --
        # rejecting them here would false-reject a publishable environment
        from experiments.models import Environment
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: grouped\n'
            '      shell: bash\n'
            '      timeout_minutes: 15\n'
            '      for_each: ["a", "b"]\n'
            '      steps:\n'
            '        - name: inner-{{ item }}\n'
            '          command: echo {{ item }}\n'
        ))
        pr = _env_pr(number=162, name='prov-group-leafkeys')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(content)), \
             patch.object(service, '_fetch_pull_request', return_value=pr):
            service.ingest_pr(162)

        recipe = Environment.objects.get(name='prov-group-leafkeys').recipe
        assert recipe.provision[0]['shell'] == 'bash'
        assert recipe.provision[0]['for_each'] == ['a', 'b']

    def test_provision_not_a_list_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, '  provision: nope\n')
        _expect_invalid_content(151, 'prov-not-list', content, 'must be a list')

    def test_provision_both_command_and_steps_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: confused\n'
            '      command: echo hi\n'
            '      steps:\n'
            '        - name: inner\n'
            '          command: echo inner\n'
        ))
        _expect_invalid_content(152, 'prov-both', content, 'sets both')

    def test_provision_neither_command_nor_steps_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: empty\n'
            '      description: does nothing\n'
        ))
        _expect_invalid_content(153, 'prov-neither', content, 'exactly one of')

    def test_provision_for_each_without_steps_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: looped-command\n'
            '      for_each: ["a", "b"]\n'
            '      command: echo {{ item }}\n'
        ))
        _expect_invalid_content(154, 'prov-loose-foreach', content, 'for_each')

    def test_provision_non_int_allow_exit_codes_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: installer\n'
            '      command: msiexec /i x.msi /qn\n'
            '      allow_exit_codes: [0, "3010"]\n'
        ))
        _expect_invalid_content(155, 'prov-bad-codes', content, 'allow_exit_codes')

    def test_provision_missing_name_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - command: echo hi\n'
        ))
        _expect_invalid_content(156, 'prov-no-name', content, 'name')

    def test_provision_unknown_shell_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: weird-shell\n'
            '      command: echo hi\n'
            '      shell: zsh\n'
        ))
        _expect_invalid_content(157, 'prov-bad-shell', content, 'shell')

    def test_provision_non_positive_timeout_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: instant\n'
            '      command: echo hi\n'
            '      timeout_minutes: 0\n'
        ))
        _expect_invalid_content(158, 'prov-bad-timeout', content, 'timeout_minutes')

    def test_provision_unknown_key_rejected(self):
        # cattrs drops unknown keys on the client, so a typo would otherwise
        # publish cleanly and then silently use the default at build time
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: typo\n'
            '      command: echo hi\n'
            '      timeout_minuts: 20\n'
        ))
        _expect_invalid_content(159, 'prov-typo-key', content, 'unknown key')

    def test_provision_nested_group_rejected(self):
        content = _recipe_with_provision(ENV_RECIPE_ONLY, (
            '  provision:\n'
            '    - name: outer\n'
            '      steps:\n'
            '        - name: inner-group\n'
            '          steps:\n'
            '            - name: deepest\n'
            '              command: echo hi\n'
        ))
        _expect_invalid_content(160, 'prov-nested', content, 'do not nest')

    def test_provision_too_many_entries_rejected(self):
        entries = ''.join(
            f'    - name: step-{i}\n      command: echo {i}\n' for i in range(60))
        content = _recipe_with_provision(ENV_RECIPE_ONLY, '  provision:\n' + entries)
        _expect_invalid_content(161, 'prov-too-many', content, 'more than')


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
        """A draft left by a closed/merged PR is reconciled; the new PR ingests 200 (no auto-close)."""
        from experiments.models import Environment
        self._ingest_env(40, 'stale-env')
        assert Request.objects.filter(gitea_pr_number=40).exists()

        # PR 40 is now closed (finalize never ran -> the draft leaked). Re-upload as PR 41.
        def _fetch(number):
            if number == 40:
                return _env_pr(40, 'stale-env', state='closed')
            return _env_pr(41, 'stale-env', state='open')

        with patch('helperfunctions.gitea_write.comment_on_pull_request') as comment, \
             patch('helperfunctions.gitea_write.close_pull_request') as close, \
             patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', side_effect=_fetch):
            service.ingest_pr(41)

        assert not Request.objects.filter(gitea_pr_number=40).exists()
        assert Request.objects.filter(gitea_pr_number=41).exists()
        assert Environment.objects.filter(name='stale-env').count() == 1
        # a stale draft is not a terminal duplicate -> never auto-closed
        comment.assert_not_called()
        close.assert_not_called()

    def test_open_pr_duplicate_rejected_and_autoclosed(self):
        """A second, still-open PR for the same name is rejected, coded, and the newer PR auto-closed."""
        from experiments.models import Environment
        self._ingest_env(50, 'dup-env')

        def _fetch(number):
            if number == 50:
                return _env_pr(50, 'dup-env', state='open')
            return _env_pr(51, 'dup-env', state='open')

        with patch('helperfunctions.gitea_write.comment_on_pull_request') as comment, \
             patch('helperfunctions.gitea_write.close_pull_request') as close, \
             patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch.object(service, '_fetch_pull_request', side_effect=_fetch):
            with pytest.raises(TaskFailure, match='#50') as exc:
                service.ingest_pr(51)

        assert exc.value.code == SubmitErrorCode.OPEN_DUPLICATE
        assert not Request.objects.filter(gitea_pr_number=51).exists()
        assert Request.objects.filter(gitea_pr_number=50).exists()
        assert Environment.objects.filter(name='dup-env').count() == 1
        # the *newer* duplicate (#51) is closed; the owning PR (#50) is never touched
        close.assert_called_once()
        assert close.call_args.args[-1] == 51
        comment.assert_called_once()
        assert comment.call_args.args[2] == 51  # (owner, repo, number, body)

    def test_published_name_collision_rejected_and_autoclosed(self):
        """Colliding with an already-published object is coded ALREADY_PUBLISHED and auto-closed."""
        from experiments.models import Environment
        self._ingest_env(60, 'pub-env')
        env = Environment.objects.get(name='pub-env')
        env.published = True
        env.save()

        with patch('helperfunctions.gitea_write.comment_on_pull_request') as comment, \
             patch('helperfunctions.gitea_write.close_pull_request') as close, \
             patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(61, 'pub-env')):
            with pytest.raises(TaskFailure, match='already published') as exc:
                service.ingest_pr(61)

        assert exc.value.code == SubmitErrorCode.ALREADY_PUBLISHED
        assert not Request.objects.filter(gitea_pr_number=61).exists()
        close.assert_called_once()
        assert close.call_args.args[-1] == 61
        comment.assert_called_once()

    def test_autoclose_disabled_by_setting(self, settings):
        """With AUTO_CLOSE_TERMINAL_DUPLICATES off, still reject+code but never touch Gitea."""
        from experiments.models import Environment
        settings.AUTO_CLOSE_TERMINAL_DUPLICATES = False
        self._ingest_env(62, 'flag-env')
        env = Environment.objects.get(name='flag-env')
        env.published = True
        env.save()

        with patch('helperfunctions.gitea_write.comment_on_pull_request') as comment, \
             patch('helperfunctions.gitea_write.close_pull_request') as close, \
             patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(63, 'flag-env')):
            with pytest.raises(TaskFailure, match='already published') as exc:
                service.ingest_pr(63)

        assert exc.value.code == SubmitErrorCode.ALREADY_PUBLISHED
        comment.assert_not_called()
        close.assert_not_called()


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


# --- modify / remove -------------------------------------------------------

CHANGED_PLAYBOOK = PLAYBOOK.replace('/tmp/test_file.txt', '/tmp/changed_file.txt')


def _modify_pr(number, name='test-experiment', merged=False, state='open'):
    pr = _pr(number=number, name=name, merged=merged, state=state)
    pr['title'] = f'[experiment modify] {name}'
    return pr


def _remove_pr(number, name='test-experiment', merged=False, state='open'):
    pr = _pr(number=number, name=name, merged=merged, state=state)
    pr['title'] = f'[experiment remove] {name}'
    return pr


def _changed_download(url, dest, **kwargs):
    if 'playbook.yml' in url:
        Path(dest).write_text(CHANGED_PLAYBOOK)
        return True
    return _fake_download(url, dest, **kwargs)


def _no_files_download(url, dest, **kwargs):
    # nothing on the branch -> simulate the remove PR having deleted the files
    return False


@pytest.mark.django_db
class TestModifyIngest:
    """Modify authors a proposed draft that coexists with the still-published object."""

    def _publish_original(self, number, name='test-experiment'):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=number, name=name)):
            service.ingest_pr(number)
        with patch.object(service, '_fetch_pull_request',
                          return_value=_pr(number=number, name=name, merged=True, state='closed')):
            service.finalize_pr(number)
        return Experiment.objects.get(name=name)

    def test_modify_creates_draft_keeps_published(self):
        original = self._publish_original(70)
        assert original.published is True

        with patch('giteaeventmanager.action.plugin.download', side_effect=_changed_download), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(71)):
            service.ingest_pr(71)

        exps = Experiment.objects.filter(name='test-experiment')
        assert exps.count() == 2
        draft = exps.get(published=False)
        published = exps.get(published=True)
        assert published.ulid == original.ulid

        req = Request.objects.get(gitea_pr_number=71)
        assert req.action == 'modify'
        assert req.object == draft
        assert req.old_object == published

    def test_modify_nonexistent_rejected(self):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_changed_download), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(72, name='ghost')):
            with pytest.raises(TaskFailure, match='does not exist'):
                service.ingest_pr(72)
        assert not Request.objects.filter(gitea_pr_number=72).exists()

    def test_modify_same_content_rejected(self):
        self._publish_original(73)
        # a modify whose content matches the published object is a no-op
        with patch.object(service, '_fetch_pull_request', return_value=_modify_pr(74)):
            with pytest.raises(TaskFailure, match='same content'):
                service.ingest_pr(74)
        assert not Request.objects.filter(gitea_pr_number=74).exists()

    def test_modify_merge_publishes_new_deletes_old(self):
        original = self._publish_original(75)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_changed_download), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(76)):
            service.ingest_pr(76)
        draft = Experiment.objects.get(name='test-experiment', published=False)

        with patch.object(service, '_fetch_pull_request',
                          return_value=_modify_pr(76, merged=True, state='closed')):
            result = service.finalize_pr(76)

        assert result['merged'] is True and result['published'] is True
        assert not Experiment.objects.filter(ulid=original.ulid).exists()
        remaining = Experiment.objects.get(name='test-experiment')
        assert remaining.ulid == draft.ulid
        assert remaining.published is True
        assert remaining.published_at is not None
        assert not Request.objects.filter(gitea_pr_number=76).exists()

    def test_modify_close_keeps_old_deletes_draft(self):
        original = self._publish_original(77)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_changed_download), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(78)):
            service.ingest_pr(78)

        with patch.object(service, '_fetch_pull_request',
                          return_value=_modify_pr(78, merged=False, state='closed')):
            result = service.finalize_pr(78)

        assert result['merged'] is False and result['deleted'] is True
        remaining = Experiment.objects.filter(name='test-experiment')
        assert remaining.count() == 1
        assert remaining.first().ulid == original.ulid
        assert remaining.first().published is True
        assert not Request.objects.filter(gitea_pr_number=78).exists()

    def test_modify_reingest_replaces_draft_keeps_old_object(self):
        original = self._publish_original(79)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_changed_download), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(80)):
            service.ingest_pr(80)
        first_draft = Experiment.objects.get(name='test-experiment', published=False)

        # re-ingest the same PR with different content -> draft replaced, old_object intact
        other_playbook = PLAYBOOK.replace('/tmp/test_file.txt', '/tmp/third_file.txt')

        def _dl(url, dest, **kwargs):
            if 'playbook.yml' in url:
                Path(dest).write_text(other_playbook)
                return True
            return _fake_download(url, dest, **kwargs)

        with patch('giteaeventmanager.action.plugin.download', side_effect=_dl), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(80)):
            service.ingest_pr(80)

        assert Request.objects.filter(gitea_pr_number=80).count() == 1
        assert Experiment.objects.filter(name='test-experiment').count() == 2
        req = Request.objects.get(gitea_pr_number=80)
        assert req.object.published is False
        assert req.object.ulid != first_draft.ulid
        assert req.old_object == original


@pytest.mark.django_db
class TestRemoveIngest:
    """Remove records a request against the still-published object; merge deletes it."""

    def _publish_original(self, number, name='test-experiment'):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=number, name=name)):
            service.ingest_pr(number)
        with patch.object(service, '_fetch_pull_request',
                          return_value=_pr(number=number, name=name, merged=True, state='closed')):
            service.finalize_pr(number)
        return Experiment.objects.get(name=name)

    def test_remove_records_request_keeps_object(self):
        self._publish_original(81)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_no_files_download), \
             patch.object(service, '_fetch_pull_request', return_value=_remove_pr(82)):
            service.ingest_pr(82)

        exp = Experiment.objects.get(name='test-experiment')
        assert exp.published is True
        req = Request.objects.get(gitea_pr_number=82)
        assert req.action == 'remove'
        assert req.object == exp

    def test_remove_with_files_present_rejected(self):
        self._publish_original(83)
        # files still on the branch -> the delete PR is malformed
        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download), \
             patch.object(service, '_fetch_pull_request', return_value=_remove_pr(84)):
            with pytest.raises(TaskFailure, match='still present'):
                service.ingest_pr(84)
        assert not Request.objects.filter(gitea_pr_number=84).exists()

    def test_remove_nonexistent_rejected(self):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_no_files_download), \
             patch.object(service, '_fetch_pull_request', return_value=_remove_pr(85, name='ghost')):
            with pytest.raises(TaskFailure, match='does not exist'):
                service.ingest_pr(85)

    def test_remove_merge_deletes_object(self):
        self._publish_original(86)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_no_files_download), \
             patch.object(service, '_fetch_pull_request', return_value=_remove_pr(87)):
            service.ingest_pr(87)

        with patch.object(service, '_fetch_pull_request',
                          return_value=_remove_pr(87, merged=True, state='closed')):
            result = service.finalize_pr(87)

        assert result['merged'] is True and result['deleted'] is True
        assert not Experiment.objects.filter(name='test-experiment').exists()
        assert not Request.objects.filter(gitea_pr_number=87).exists()

    def test_remove_close_keeps_object(self):
        self._publish_original(88)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_no_files_download), \
             patch.object(service, '_fetch_pull_request', return_value=_remove_pr(89)):
            service.ingest_pr(89)

        with patch.object(service, '_fetch_pull_request',
                          return_value=_remove_pr(89, merged=False, state='closed')):
            result = service.finalize_pr(89)

        assert result['merged'] is False and result['deleted'] is False
        assert Experiment.objects.filter(name='test-experiment').exists()
        assert not Request.objects.filter(gitea_pr_number=89).exists()


def _env_modify_pr(number, name, merged=False, state='open'):
    pr = _env_pr(number, name, merged=merged, state=state)
    pr['title'] = f'[environment modify] {name}'
    return pr


@pytest.mark.django_db
class TestEnvironmentModify:
    """Environments have a (formerly unique) name; modify must let a draft coexist."""

    def _publish_env(self, number, name):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(number, name)):
            service.ingest_pr(number)
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request',
                          return_value=_env_pr(number, name, merged=True, state='closed')):
            service.finalize_pr(number)

    def test_modify_allows_two_same_name_rows(self):
        from experiments.models import Environment
        self._publish_env(90, 'modenv')
        assert Environment.objects.get(name='modenv').published is True

        changed_env = ENV_VM.replace('Adare-Ubuntu2204.ova', 'Adare-Ubuntu2404.ova')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(changed_env)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=_env_modify_pr(91, 'modenv')):
            service.ingest_pr(91)

        # the relaxed unique constraint lets the draft coexist with the published env
        assert Environment.objects.filter(name='modenv').count() == 2
        req = Request.objects.get(gitea_pr_number=91)
        assert req.action == 'modify'
        assert req.old_object.published is True
        assert req.object.published is False

        # merge -> new published, old gone, single row again
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(changed_env)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request',
                          return_value=_env_modify_pr(91, 'modenv', merged=True, state='closed')):
            service.finalize_pr(91)

        remaining = Environment.objects.filter(name='modenv')
        assert remaining.count() == 1
        assert remaining.first().published is True
        assert remaining.first().vm.endswith('Adare-Ubuntu2404.ova')


# --- error codes -----------------------------------------------------------


@pytest.mark.django_db
class TestErrorCodes:
    """Every ingest failure carries a machine-readable SubmitErrorCode."""

    def test_unknown_environment_is_unknown_dependency(self):
        bad_metadata = 'environments:\n  - does-not-exist\ntags: []\n'

        def _dl(url, dest, **kwargs):
            if 'metadata.yml' in url:
                Path(dest).write_text(bad_metadata)
                return True
            return _fake_download(url, dest, **kwargs)

        with patch('giteaeventmanager.action.plugin.download', side_effect=_dl), \
             patch.object(service, '_fetch_pull_request', return_value=_pr(number=100)):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(100)
        assert exc.value.code == SubmitErrorCode.UNKNOWN_DEPENDENCY

    def test_missing_vm_source_is_invalid_content(self):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_NO_SOURCE)), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(101, 'badenv2')):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(101)
        assert exc.value.code == SubmitErrorCode.INVALID_CONTENT

    def test_invalid_recipe_is_invalid_content(self):
        # recipe envs are now a supported source; a malformed recipe (non-hex
        # iso_sha256) is the recipe-branch validation failure that must carry
        # INVALID_CONTENT.
        bad_recipe = ENV_RECIPE_ONLY.replace(RECIPE_ISO_SHA256, 'nothex')
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(bad_recipe)), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(102, 'recipeenv2')):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(102)
        assert exc.value.code == SubmitErrorCode.INVALID_CONTENT

    def test_modify_nonexistent_is_not_found(self):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_changed_download), \
             patch.object(service, '_fetch_pull_request', return_value=_modify_pr(103, name='ghost2')):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(103)
        assert exc.value.code == SubmitErrorCode.NOT_FOUND

    def test_remove_nonexistent_is_not_found(self):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_no_files_download), \
             patch.object(service, '_fetch_pull_request', return_value=_remove_pr(104, name='ghost3')):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(104)
        assert exc.value.code == SubmitErrorCode.NOT_FOUND

    def test_unparseable_title_is_parse_error(self):
        pr = _pr(number=105)
        pr['title'] = 'not a valid title'
        with patch.object(service, '_fetch_pull_request', return_value=pr):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(105)
        assert exc.value.code == SubmitErrorCode.PARSE_ERROR

    def test_fetch_failure_is_upstream_unavailable(self):
        class _Resp:
            status_code = 502
            text = 'bad gateway'

        with patch('giteaeventmanager.service.GiteaAuthHandle.get_token', return_value='tok'), \
             patch('giteaeventmanager.service.requests.get', return_value=_Resp()):
            with pytest.raises(TaskFailure) as exc:
                service._fetch_pull_request(106)
        assert exc.value.code == SubmitErrorCode.UPSTREAM_UNAVAILABLE

    def test_content_duplicate_is_coded_and_not_autoclosed(self):
        with patch.object(service, '_fetch_pull_request', return_value=_pr(number=107, name='dupcontent')):
            service.ingest_pr(107)
        with patch('helperfunctions.gitea_write.comment_on_pull_request') as comment, \
             patch('helperfunctions.gitea_write.close_pull_request') as close, \
             patch.object(service, '_fetch_pull_request', return_value=_pr(number=108, name='dupcontent2')):
            with pytest.raises(TaskFailure) as exc:
                service.ingest_pr(108)
        assert exc.value.code == SubmitErrorCode.CONTENT_DUPLICATE
        # content duplicate is fixable, not terminal -> never auto-closed
        comment.assert_not_called()
        close.assert_not_called()


# --- pre-submit classification --------------------------------------------


@pytest.mark.django_db
class TestClassifySubmission:
    """Name-based classification used by the CLI/React pre-check (no Gitea calls)."""

    def test_unknown_name_is_ok(self):
        assert service.classify_submission('environment', 'nope-env')['code'] == SubmitErrorCode.OK

    def test_published_is_already_published(self):
        from experiments.models import Environment
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(110, 'classpub')):
            service.ingest_pr(110)
        env = Environment.objects.get(name='classpub')
        env.published = True
        env.save()

        result = service.classify_submission('environment', 'classpub')
        assert result['code'] == SubmitErrorCode.ALREADY_PUBLISHED

    def test_open_draft_is_open_duplicate(self):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(111, 'classdraft')):
            service.ingest_pr(111)

        result = service.classify_submission('environment', 'classdraft')
        assert result['code'] == SubmitErrorCode.OPEN_DUPLICATE
        assert result['pr_number'] == 111

    def test_unknown_entity_type_raises_parse_error(self):
        with pytest.raises(TaskFailure) as exc:
            service.classify_submission('bogus', 'x')
        assert exc.value.code == SubmitErrorCode.PARSE_ERROR


# --- React proxy: pre-check before PR + reuse open PR ----------------------


@pytest.mark.django_db
class TestSubmitViews:
    """submit_views pre-checks a create *before* opening a PR and reuses an open PR."""

    def test_create_published_returns_409_without_opening_pr(self):
        import experiments.submit_views as submit_views
        from experiments.models import Environment
        with patch('giteaeventmanager.action.plugin.download', side_effect=_env_download(ENV_VM)), \
             patch('giteaeventmanager.action.plugin.requests.head', return_value=_OkResp()), \
             patch.object(service, '_fetch_pull_request', return_value=_env_pr(120, 'viewpub')):
            service.ingest_pr(120)
        env = Environment.objects.get(name='viewpub')
        env.published = True
        env.save()

        with patch('experiments.submit_views.create_branch') as create_branch, \
             patch('experiments.submit_views.create_pull_request') as create_pr, \
             patch('experiments.submit_views.find_open_pull_request') as find_pr, \
             patch('experiments.submit_views.ingest_pr') as ingest:
            body, status = submit_views._submit_and_ingest(
                entity_type='environment', name='viewpub',
                files={'environments/viewpub.yml': b'x'}, username='u', description='')

        assert status == 409
        assert body['code'] == SubmitErrorCode.ALREADY_PUBLISHED
        create_branch.assert_not_called()
        create_pr.assert_not_called()
        find_pr.assert_not_called()
        ingest.assert_not_called()

    def test_submit_files_reuses_open_create_pr(self):
        import experiments.submit_views as submit_views
        existing = {'number': 200, 'html_url': 'http://gitea/pr/200',
                    'head': {'ref': 'submit/environment/reuse-me-20240101'}}
        with patch('experiments.submit_views.find_open_pull_request', return_value=existing), \
             patch('experiments.submit_views.create_branch') as create_branch, \
             patch('experiments.submit_views.create_pull_request') as create_pr, \
             patch('experiments.submit_views.upload_file', return_value=True) as upload:
            pr = submit_views._submit_files(
                entity_type='environment', name='reuse-me',
                files={'environments/reuse-me.yml': b'data'}, username='u', action='create')

        assert pr is existing
        create_branch.assert_not_called()
        create_pr.assert_not_called()
        upload.assert_called_once()
        # uploaded onto the reused PR's branch, not a fresh timestamped one
        assert upload.call_args.args[4] == 'submit/environment/reuse-me-20240101'

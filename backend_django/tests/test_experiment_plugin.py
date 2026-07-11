from pathlib import Path
from unittest.mock import patch

import pytest

from giteaeventmanager.action.plugin import ExperimentPlugin
from tests.factories import EnvironmentFactory, GiteaUserFactory, TestFunctionFactory, TestParameterFactory


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


@pytest.mark.django_db
class TestExperimentPluginDownload:

    def test_fetches_playbook_and_metadata(self, settings):
        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin = ExperimentPlugin('download-test', 'test-experiment', 'deadbeef')
            downloaded, missing = plugin.download()
        assert missing == []
        assert plugin.playbook_file is not None and plugin.playbook_file.name == 'playbook.yml'
        assert plugin.metadata_file is not None and plugin.metadata_file.name == 'metadata.yml'
        assert 'experiments/test-experiment/playbook.yml' in plugin.playbookfile_remote_url


@pytest.mark.django_db
class TestExperimentPluginUpdateObject:

    def test_full_create_path(self, settings):
        environment = EnvironmentFactory(name='test-env')
        TestFunctionFactory(name='is_file')
        TestParameterFactory(name='path')
        user = GiteaUserFactory()

        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin = ExperimentPlugin('update-test', 'test-experiment', 'deadbeef')
            plugin.download()
            plugin.hash()
            exp = plugin.update_object(published_by=user)

        assert exp.playbook_file == plugin.playbookfile_remote_url
        assert exp.sha256playbook == plugin.playbook_sha256
        assert exp.sha256hash == plugin.sha256
        assert exp.abstract_tests.count() == 1
        assert exp.abstract_tests.first().name == 'check-file-exists'
        assert list(exp.environments.all()) == [environment]

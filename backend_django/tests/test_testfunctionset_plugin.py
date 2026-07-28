from pathlib import Path
from unittest.mock import patch

import pytest

from experiments.models import AbstractTest, TestfunctionSet, TestFunction
from giteaeventmanager.action.plugin import TestfunctionsetPlugin
from giteaeventmanager.action.base import PRIngestModify
from giteaeventmanager.errorcodes import SubmitErrorCode
from giteaeventmanager.exception import TaskFailure
from tests.factories import AbstractTestFactory, ExperimentFactory, GiteaUserFactory


TFSET_V1 = (
    'class IsFileParams:\n'
    '    path: str = ""\n\n\n'
    'class IsFile(BasicTest):\n'
    '    testname: str = "is_file"\n'
    '    testdescription: str = "Check if a file exists"\n'
    '    params: IsFileParams\n'
)
TFSET_V2 = TFSET_V1.replace('Check if a file exists', 'Check if a file exists (v2)')
REQUIREMENTS = ''


def _fake_download(content):
    def _download(url, dest, **kwargs):
        if 'requirements.txt' in url:
            Path(dest).write_text(REQUIREMENTS)
            return True
        Path(dest).write_text(content)
        return True
    return _download


def _ingest_json(pr_number, sha='deadbeef'):
    return {
        'number': pr_number,
        'pull_request': {'title': 'modify tfset', 'head': {'sha': sha}},
    }


@pytest.mark.django_db
class TestTestfunctionsetPluginVersioning:
    def test_first_publish_starts_at_version_1_not_current(self):
        user = GiteaUserFactory()
        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download(TFSET_V1)), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin = TestfunctionsetPlugin('create-test', 'my-set', 'deadbeef')
            plugin.download()
            plugin.hash()
            tfset = plugin.update_object(published_by=user)

        assert tfset.version == 1
        assert tfset.is_current is False

    def test_modify_increments_version_and_demote_keeps_old_row(self):
        user = GiteaUserFactory()

        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download(TFSET_V1)), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin_v1 = TestfunctionsetPlugin('create-test', 'my-set', 'deadbeef')
            plugin_v1.download()
            plugin_v1.hash()
            v1 = plugin_v1.update_object(published_by=user)

        # simulate the create PR merging: v1 becomes published + current
        v1.published = True
        v1.is_current = True
        v1.save()

        # regression check for the CASCADE-delete risk: an Experiment references
        # a TestFunction/AbstractTest that lives on v1
        abstract_test = AbstractTestFactory(testfunction=v1.testfunctions.get(name='is_file'))
        experiment = ExperimentFactory(abstract_tests=[abstract_test])

        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download(TFSET_V2)), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin_v2 = TestfunctionsetPlugin('modify-test', 'my-set', 'cafebabe')
            plugin_v2.download()
            plugin_v2.hash()
            v2 = plugin_v2.update_object(published_by=user)

        assert v2.version == 2
        assert v2.is_current is False

        # simulate the modify PR merging: v2 becomes current, v1 is demoted (not deleted)
        plugin_v2.demote_superseded(v1)
        v2.published = True
        v2.is_current = True
        v2.save()

        v1.refresh_from_db()
        assert v1.is_current is False
        assert v1.published is True  # demote_superseded only flips is_current

        # old row (and everything cascading from it) must still exist
        assert TestfunctionSet.objects.filter(ulid=v1.ulid).exists()
        assert TestFunction.objects.filter(testfunction_set=v1).exists()
        assert AbstractTest.objects.filter(ulid=abstract_test.ulid).exists()
        experiment.refresh_from_db()
        assert abstract_test in experiment.abstract_tests.all()

        # get_object() (current-version-aware) now resolves to v2
        assert plugin_v2.get_object() == v2

        # v1 is still individually fetchable by ulid/hash
        assert TestfunctionSet.objects.get(ulid=v1.ulid).sha256hash == v1.sha256hash

    def test_republishing_identical_content_is_rejected_as_content_duplicate(self):
        user = GiteaUserFactory()
        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download(TFSET_V1)), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin_v1 = TestfunctionsetPlugin('create-test', 'my-set', 'deadbeef')
            plugin_v1.download()
            plugin_v1.hash()
            v1 = plugin_v1.update_object(published_by=user)

        v1.published = True
        v1.is_current = True
        v1.save()

        with patch('giteaeventmanager.action.plugin.download', side_effect=_fake_download(TFSET_V1)), \
             patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
            plugin_dup = TestfunctionsetPlugin('modify-test', 'my-set', 'cafebabe')
            ingest = PRIngestModify(plugin_dup, _ingest_json(1), 'testfunctionset', 'modify', 'my-set')
            with pytest.raises(TaskFailure) as excinfo:
                ingest.check()

        assert excinfo.value.code == SubmitErrorCode.CONTENT_DUPLICATE

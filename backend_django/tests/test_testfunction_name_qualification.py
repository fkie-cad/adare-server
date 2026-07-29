"""Regression tests for the `<set>.<name>` identity of a TestFunction.

Registration (TestfunctionsetPlugin) and experiment ingest (ExperimentPlugin)
have to agree on one name format. The playbook's `function:` string is the
qualified `<set>.<name>` form (an unprefixed name means the `standard` set --
see the client's adarelib.testset.testfunction.get_testclass_from_testfunction),
so that is the form the DB stores and the form ingest looks up.
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from experiments.models import TestFunction, TestfunctionSet
from giteaeventmanager.action.plugin import ExperimentPlugin, TestfunctionsetPlugin
from giteaeventmanager.errorcodes import SubmitErrorCode
from giteaeventmanager.exception import TaskFailure
from tests.factories import EnvironmentFactory, GiteaUserFactory, TestParameterFactory


# A decorator-style module, as the client's real testfunction sets are written
# (adare/appdata/testfunctions/jsonl/jsonl.py). `name=` is bare.
JSONL_MODULE = (
    'from adarelib.testset.api import testfunction, TestContext\n\n\n'
    "@testfunction(\n"
    "    name='line_matches',\n"
    "    description='tests if lines in a JSONL file match conditions',\n"
    ")\n"
    "def line_matches(ctx: TestContext, dst: str = '', match_mode: str = 'any'):\n"
    '    return True\n'
)
# Two sets both declaring `compare_rows` -- the bare name is not unique.
CSV_MODULE = (
    'from adarelib.testset.api import testfunction, TestContext\n\n\n'
    "@testfunction(name='compare_rows', description='compare csv rows')\n"
    "def compare_rows(ctx: TestContext, dst: str = ''):\n"
    '    return True\n'
)
EXCEL_MODULE = (
    'from adarelib.testset.api import testfunction, TestContext\n\n\n'
    "@testfunction(name='compare_rows', description='compare excel rows')\n"
    "def compare_rows(ctx: TestContext, dst: str = ''):\n"
    '    return True\n'
)
# The shipped `visual` set declares names that already carry the set prefix.
VISUAL_MODULE = (
    'from adarelib.testset.api import testfunction\n\n\n'
    "@testfunction(name='visual.exists', description='text or image on screen')\n"
    "def visual_exists(ctx, text: str = ''):\n"
    '    return True\n'
)
# An unparseable/empty `name=` -- must be rejected, not silently registered as
# `<set>.` (the same shape of bug qualify_test_name exists to fix, one level up).
EMPTY_NAME_MODULE = (
    'from adarelib.testset.api import testfunction, TestContext\n\n\n'
    "@testfunction(name='', description='name failed to parse')\n"
    "def mystery(ctx: TestContext):\n"
    '    return True\n'
)


def _tfset_download(content):
    def _download(url, dest, **kwargs):
        if 'requirements.txt' in url:
            Path(dest).write_text('')
            return True
        Path(dest).write_text(content)
        return True
    return _download


def _ingest_tfset(set_name, module_source, user, commit='deadbeef'):
    """Ingest a set and simulate its PR merging (published + current).

    Demotes any previous current row first: `unique_tf_current_per_name` allows
    only one is_current=True per name, and PRFinalize demotes before promoting.
    """
    with patch('giteaeventmanager.action.plugin.download', side_effect=_tfset_download(module_source)), \
         patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
        plugin = TestfunctionsetPlugin('create-test', set_name, commit)
        plugin.download()
        plugin.hash()
        tfset = plugin.update_object(published_by=user)
    TestfunctionSet.objects.filter(name=set_name, is_current=True).update(is_current=False)
    tfset.published = True
    tfset.is_current = True
    tfset.save()
    return tfset


def _playbook(function, test_name='check'):
    return (
        'name: exp\n'
        'tests:\n'
        f'  - name: {test_name}\n'
        '    description: d\n'
        f'    function: {function}\n'
        '    parameter:\n'
        '      dst: /tmp/out.jsonl\n'
        'actions:\n'
        f'  - test: {test_name}\n'
    )


def _experiment_download(playbook, metadata):
    def _download(url, dest, **kwargs):
        if 'playbook.yml' in url:
            Path(dest).write_text(playbook)
            return True
        if 'metadata.yml' in url:
            Path(dest).write_text(metadata)
            return True
        return False
    return _download


def _ingest_experiment(function, user, env_name, name='exp-1'):
    metadata = f'environments:\n  - {env_name}\ntags: []\n'
    with patch('giteaeventmanager.action.plugin.download',
               side_effect=_experiment_download(_playbook(function), metadata)), \
         patch('giteaeventmanager.action.plugin.GiteaAuthHandle.get_token', return_value='tok'):
        plugin = ExperimentPlugin('create-test', name, 'cafebabe')
        plugin.download()
        plugin.hash()
        return plugin.update_object(published_by=user)


@pytest.mark.django_db
class TestRegistrationStoresQualifiedNames:

    def test_bare_decorator_name_is_qualified_with_the_set(self):
        user = GiteaUserFactory()
        tfset = _ingest_tfset('jsonl', JSONL_MODULE, user)

        names = list(tfset.testfunctions.values_list('name', flat=True))
        assert names == ['jsonl.line_matches']
        # the AST class name still lands in `type`, unchanged
        assert tfset.testfunctions.get().type == '_DecoratorTest_line_matches'

    def test_already_qualified_decorator_name_is_not_double_qualified(self):
        user = GiteaUserFactory()
        tfset = _ingest_tfset('visual', VISUAL_MODULE, user)

        names = list(tfset.testfunctions.values_list('name', flat=True))
        assert names == ['visual.exists']
        assert 'visual.visual.exists' not in names

    def test_same_bare_name_in_two_sets_stays_distinguishable(self):
        user = GiteaUserFactory()
        csv_set = _ingest_tfset('csv', CSV_MODULE, user, commit='aaa')
        excel_set = _ingest_tfset('excel', EXCEL_MODULE, user, commit='bbb')

        assert csv_set.testfunctions.get().name == 'csv.compare_rows'
        assert excel_set.testfunctions.get().name == 'excel.compare_rows'

    def test_reingest_of_the_same_set_updates_within_the_new_version(self):
        """Each ingest is a new TestfunctionSet version (0015), so each version
        owns its own TestFunction row; the guard must not collide inside one."""
        user = GiteaUserFactory()
        v1 = _ingest_tfset('jsonl', JSONL_MODULE, user, commit='aaa')
        changed = JSONL_MODULE.replace('match conditions', 'match conditions (v2)')
        v2 = _ingest_tfset('jsonl', changed, user, commit='bbb')

        assert v2.version == v1.version + 1
        assert v1.testfunctions.count() == 1
        assert v2.testfunctions.count() == 1
        assert v2.testfunctions.get().description.endswith('(v2)')

    def test_empty_decorator_name_is_rejected_not_silently_registered(self):
        """An unparseable/empty `name=` must fail loudly, not register `<set>.`
        (qualify_test_name would otherwise happily prefix an empty string)."""
        user = GiteaUserFactory()

        with pytest.raises(TaskFailure) as exc_info:
            _ingest_tfset('mystery', EMPTY_NAME_MODULE, user)

        assert exc_info.value.code == SubmitErrorCode.INVALID_CONTENT
        assert not TestFunction.objects.filter(name__startswith='mystery.').exists()


@pytest.mark.django_db
class TestExperimentIngestResolvesPlaybookFunctions:

    def test_qualified_function_resolves(self):
        """The live PR #224 failure: `jsonl.line_matches does not exist`."""
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        TestParameterFactory(name='dst')
        _ingest_tfset('jsonl', JSONL_MODULE, user)

        experiment = _ingest_experiment('jsonl.line_matches', user, env.name)

        abstract_test = experiment.abstract_tests.get()
        assert abstract_test.testfunction.name == 'jsonl.line_matches'

    def test_unprefixed_function_resolves_against_the_standard_set(self):
        """pecmd's first three tests are unprefixed (`file_exists`, ...); the
        client resolves those against `standard`, so ingest must too."""
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        TestParameterFactory(name='dst')
        standard_module = JSONL_MODULE.replace('line_matches', 'file_exists')
        _ingest_tfset('standard', standard_module, user)

        experiment = _ingest_experiment('file_exists', user, env.name)

        assert experiment.abstract_tests.get().testfunction.name == 'standard.file_exists'

    def test_qualified_function_picks_the_right_set_on_a_name_collision(self):
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        TestParameterFactory(name='dst')
        csv_set = _ingest_tfset('csv', CSV_MODULE, user, commit='aaa')
        excel_set = _ingest_tfset('excel', EXCEL_MODULE, user, commit='bbb')

        from_csv = _ingest_experiment('csv.compare_rows', user, env.name, name='exp-csv')
        from_excel = _ingest_experiment('excel.compare_rows', user, env.name, name='exp-excel')

        assert from_csv.abstract_tests.get().testfunction.testfunction_set == csv_set
        assert from_excel.abstract_tests.get().testfunction.testfunction_set == excel_set

    def test_resolves_to_the_current_set_version_not_the_oldest(self):
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        TestParameterFactory(name='dst')
        v1 = _ingest_tfset('jsonl', JSONL_MODULE, user, commit='aaa')
        changed = JSONL_MODULE.replace('match conditions', 'match conditions (v2)')
        v2 = _ingest_tfset('jsonl', changed, user, commit='bbb')
        v1.refresh_from_db()
        assert v1.is_current is False and v2.is_current is True

        experiment = _ingest_experiment('jsonl.line_matches', user, env.name)

        assert experiment.abstract_tests.get().testfunction.testfunction_set == v2

    def test_falls_back_to_the_highest_version_when_none_is_current(self):
        """Exercises the cross-FK ordering in the fallback branch."""
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        TestParameterFactory(name='dst')
        _ingest_tfset('jsonl', JSONL_MODULE, user, commit='aaa')
        changed = JSONL_MODULE.replace('match conditions', 'match conditions (v2)')
        v2 = _ingest_tfset('jsonl', changed, user, commit='bbb')
        TestfunctionSet.objects.filter(name='jsonl').update(is_current=False)

        experiment = _ingest_experiment('jsonl.line_matches', user, env.name)

        assert experiment.abstract_tests.get().testfunction.testfunction_set == v2

    def test_unknown_function_still_fails_loudly(self):
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        _ingest_tfset('jsonl', JSONL_MODULE, user)

        with pytest.raises(TaskFailure) as excinfo:
            _ingest_experiment('jsonl.nope', user, env.name)

        assert excinfo.value.code == SubmitErrorCode.UNKNOWN_DEPENDENCY

    def test_a_bare_reference_to_a_non_standard_set_is_rejected(self):
        """`line_matches` without the `jsonl.` prefix means `standard.line_matches`
        to the client, so ingest must not silently bind it to the jsonl set."""
        user = GiteaUserFactory()
        env = EnvironmentFactory(name='test-env')
        _ingest_tfset('jsonl', JSONL_MODULE, user)

        with pytest.raises(TaskFailure) as excinfo:
            _ingest_experiment('line_matches', user, env.name)

        assert excinfo.value.code == SubmitErrorCode.UNKNOWN_DEPENDENCY
        assert TestFunction.objects.filter(name='standard.line_matches').count() == 0

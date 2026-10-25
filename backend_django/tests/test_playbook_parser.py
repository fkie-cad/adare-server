import re
from pathlib import Path

import pytest
import yaml

from testsetfile.parser import parse_playbook_tests


def _write(tmp_path, text):
    p = tmp_path / 'playbook.yml'
    p.write_text(text)
    return p


class TestParsePlaybookTests:

    def test_maps_function_and_parameter(self, tmp_path):
        pb = _write(tmp_path, (
            'tests:\n'
            '  - name: t1\n'
            '    description: desc\n'
            '    function: file_exists\n'
            '    parameter:\n'
            '      dst: "{{filepath}}"\n'
            'actions:\n'
            '  - test: t1\n'
        ))
        result = parse_playbook_tests(pb, 'my-exp')
        assert result.name == 'my-exp'
        assert len(result.tests) == 1
        t = result.tests[0]
        assert t.name == 't1'
        assert t.description == 'desc'
        assert t.type == 'file_exists'
        assert '{{filepath}}' in str(t.params['dst'])

    def test_missing_tests_returns_empty_list(self, tmp_path):
        assert parse_playbook_tests(_write(tmp_path, 'actions: []\n'), 'e').tests == []

    def test_empty_tests_returns_empty_list(self, tmp_path):
        assert parse_playbook_tests(_write(tmp_path, 'tests: []\n'), 'e').tests == []

    def test_actions_are_ignored(self, tmp_path):
        pb = _write(tmp_path, (
            'tests:\n'
            '  - name: t1\n'
            '    description: desc\n'
            '    function: is_file\n'
            '    parameter:\n'
            '      path: /tmp/x\n'
            'actions:\n'
            '  - test: t1\n'
            '  - test: does-not-exist\n'
        ))
        result = parse_playbook_tests(pb, 'e')
        assert len(result.tests) == 1
        assert result.tests[0].name == 't1'


TAG_TESTS = (
    'tests:\n'
    '  - name: t\n'
    '    function: csv.contains_line\n'
    '    parameter:\n'
    '      entry:\n'
    '        - {tag}\n'
)


class TestTimestampTags:
    """The server must read every `!timestamp` form the client accepts (adarelib customtags)."""

    def _param(self, tmp_path, tag):
        result = parse_playbook_tests(_write(tmp_path, TAG_TESTS.format(tag=tag)), 'e')
        return result.tests[0].params['entry'][0]

    def test_tolerance_form(self, tmp_path):
        tag = self._param(tmp_path, "!timestamp {timestamp: '{{ t }}', tolerance: 5}")
        assert repr(tag) == '!timestamp {timestamp: {{ t }}, tolerance: 5}'

    def test_timezone_and_format_form(self, tmp_path):
        # The paper's Windows Recycle Bin demo uses this form.
        tag = self._param(tmp_path, "!timestamp {timestamp: '{{ t }}', tolerance: 5, timezone: utc, format: '%Y'}")
        assert tag.options == {'tolerance': 5, 'timezone': 'utc', 'format': '%Y'}

    def test_interval_form(self, tmp_path):
        tag = self._param(
            tmp_path, "!timestamp {after: '{{ t0 }}', before: '{{ t1 }}', precision: 1, localtime: true}")
        assert repr(tag) == '!timestamp {after: {{ t0 }}, before: {{ t1 }}, precision: 1, localtime: True}'
        assert tag.string == '{{ t0 }}'

    def test_timestamp_named_by_first_key(self, tmp_path):
        tag = self._param(tmp_path, "!timestamp {'{{ t }}': null, tolerance: 2}")
        assert tag.timestamp == '{{ t }}' and tag.options == {'tolerance': 2}

    def test_str_of_params_keeps_the_comparison(self, tmp_path):
        # Parameters are stored as str(value): an interval must not look like an exact value.
        result = parse_playbook_tests(_write(tmp_path, TAG_TESTS.format(
            tag="!timestamp {after: '{{ t0 }}', before: '{{ t1 }}'}")), 'e')
        assert 'after: {{ t0 }}' in str(result.tests[0].params['entry'])

    @pytest.mark.parametrize(('tag', 'message'), [
        ("!timestamp {timestamp: '{{ t }}', tolerace: 5}", 'unknown option(s) tolerace'),
        ("!timestamp {after: '{{ t0 }}'}", 'needs both after and before'),
        ("!timestamp {tolerance: 5}", 'needs a timestamp'),
    ])
    def test_invalid_tag_is_a_yaml_error(self, tmp_path, tag, message):
        with pytest.raises(yaml.YAMLError, match=re.escape(message)):
            parse_playbook_tests(_write(tmp_path, TAG_TESTS.format(tag=tag)), 'e')

    def test_ingest_reports_a_bad_tag_as_invalid_content(self, tmp_path):
        # Parsing fails before any database access, so no db fixture is needed.
        from giteaeventmanager.action.plugin import ExperimentPlugin
        from giteaeventmanager.errorcodes import SubmitErrorCode
        from giteaeventmanager.exception import TaskFailure

        playbook = _write(tmp_path, TAG_TESTS.format(tag="!timestamp {after: '{{ t0 }}'}"))
        plugin = ExperimentPlugin('bad-tag', 'exp', 'deadbeef')
        with pytest.raises(TaskFailure, match='needs both after and before') as failure:
            plugin._ExperimentPlugin__db_create_abstracttests_from_playbook(playbook)
        assert failure.value.code == SubmitErrorCode.INVALID_CONTENT

    def test_dumps_back_to_the_same_tag(self):
        from customyaml.customloader import create_yaml_loader_dumper_inputfiles
        from customyaml.customtags import YamlTimestamp

        loader, dumper = create_yaml_loader_dumper_inputfiles()
        tag = YamlTimestamp(after='{{ t0 }}', before='{{ t1 }}', precision=1)
        again = yaml.load(yaml.dump(tag, Dumper=dumper), Loader=loader)
        assert (again.timestamp, again.options) == (None, tag.options)

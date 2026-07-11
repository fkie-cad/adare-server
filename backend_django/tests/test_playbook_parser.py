from pathlib import Path

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

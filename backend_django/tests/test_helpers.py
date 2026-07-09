import hashlib
import tempfile
from pathlib import Path

import pytest
from unittest.mock import patch

from helperfunctions.hash import hash_file_sha256, combine_hashes
from helperfunctions.requirements import parse_requirements_from_file, check_if_requirements_file_is_valid
from helperfunctions.yaml import yaml_to_dict


class TestHashFileSha256:

    def test_known_content(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_bytes(b'hello world')
        expected = hashlib.sha256(b'hello world').hexdigest()
        assert hash_file_sha256(f) == expected

    def test_empty_file(self, tmp_path):
        f = tmp_path / 'empty.txt'
        f.write_bytes(b'')
        expected = hashlib.sha256(b'').hexdigest()
        assert hash_file_sha256(f) == expected


class TestCombineHashes:

    def test_deterministic(self):
        h1 = hashlib.sha256(b'a').hexdigest()
        h2 = hashlib.sha256(b'b').hexdigest()
        result1 = combine_hashes([h1, h2])
        result2 = combine_hashes([h1, h2])
        assert result1 == result2

    def test_order_matters(self):
        h1 = hashlib.sha256(b'a').hexdigest()
        h2 = hashlib.sha256(b'b').hexdigest()
        assert combine_hashes([h1, h2]) != combine_hashes([h2, h1])

    def test_single_hash(self):
        h = hashlib.sha256(b'x').hexdigest()
        result = combine_hashes([h])
        expected = hashlib.sha256(h.encode()).hexdigest()
        assert result == expected


class TestParseRequirementsFromFile:

    def test_basic_requirements(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('requests>=2.28\nnumpy==1.24.0\n')
        reqs = parse_requirements_from_file(f)
        assert len(reqs) == 2
        assert reqs[0].package == 'requests'
        assert reqs[0].relation == '>='
        assert reqs[0].version == '2.28'
        assert reqs[1].package == 'numpy'

    def test_package_only(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('flask\n')
        reqs = parse_requirements_from_file(f)
        assert len(reqs) == 1
        assert reqs[0].package == 'flask'
        assert reqs[0].version == ''
        assert reqs[0].relation == ''

    def test_comments_and_blanks_skipped(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('# comment\n\nflask\n# another\n')
        reqs = parse_requirements_from_file(f)
        assert len(reqs) == 1

    def test_empty_file(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('')
        reqs = parse_requirements_from_file(f)
        assert reqs == []


class TestCheckRequirementsFileIsValid:

    def test_valid_file(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('requests>=2.28\nnumpy\n')
        assert check_if_requirements_file_is_valid(f) is True

    def test_empty_file(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('')
        assert check_if_requirements_file_is_valid(f) is True

    def test_invalid_file(self, tmp_path):
        f = tmp_path / 'requirements.txt'
        f.write_text('this is not a valid requirement!@#$\n')
        assert check_if_requirements_file_is_valid(f) is False


class TestGiteaUrlConversion:

    @pytest.fixture(autouse=True)
    def _settings(self, settings):
        settings.GITEA_URL = 'https://gitea.example.com/'
        settings.GITEA_INTERNAL_URL = 'http://gitea:3000/'

    def test_convert_internal_to_viewable(self):
        from helperfunctions.gitea import convert_gitea_internal_api_url_to_viewable_url
        url = 'http://gitea:3000/api/v1/repos/miq/adareTEST/raw/experiments/test/action.py?ref=main'
        result = convert_gitea_internal_api_url_to_viewable_url(url)
        assert 'https://gitea.example.com/' in result
        assert '/src/branch/main/' in result
        assert 'api/v1' not in result

    def test_convert_internal_to_external(self):
        from helperfunctions.gitea import convert_gitea_internal_api_url_to_external
        url = 'http://gitea:3000/api/v1/repos/miq/adareTEST/raw/experiments/test/action.py?ref=main'
        result = convert_gitea_internal_api_url_to_external(url)
        assert result.startswith('https://gitea.example.com/')
        assert 'api/v1' in result


class TestYamlToDict:

    def test_valid_yaml(self, tmp_path):
        f = tmp_path / 'test.yml'
        f.write_text('name: test\nvalue: 42\n')
        result = yaml_to_dict(f)
        assert result == {'name': 'test', 'value': 42}

    def test_list_yaml(self, tmp_path):
        f = tmp_path / 'test.yml'
        f.write_text('- a\n- b\n- c\n')
        result = yaml_to_dict(f)
        assert result == ['a', 'b', 'c']

    def test_empty_yaml(self, tmp_path):
        f = tmp_path / 'test.yml'
        f.write_text('')
        result = yaml_to_dict(f)
        assert result is None

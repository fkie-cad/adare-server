import hashlib

import pytest

from tests.factories import (
    ExperimentFactory,
    EnvironmentFactory,
    TestfunctionSetFactory,
)


def _experiment_hash_url(sha256hash):
    return f"/api/hash/experiment_{sha256hash}/"


def _environment_hash_url(sha256hash):
    return f"/api/hash/environment_{sha256hash}/"


def _testfunction_hash_url(sha256hash):
    return f"/api/hash/testfunction_{sha256hash}/"


@pytest.mark.django_db
class TestHashEndpoints:
    def test_experiment_hash_to_metadata(self, api_client):
        exp = ExperimentFactory(published=True)

        # The client (adare/webappaccess/download.py) sends only the
        # playbook hash (ExperimentDirectory.sha256), not the combined
        # playbook+metadata sha256hash, so the endpoint must look up by
        # sha256playbook.
        resp = api_client.get(_experiment_hash_url(exp.sha256playbook))

        assert resp.status_code == 200
        assert resp.data["ulid"] == exp.ulid
        assert resp.data["published"] is True
        assert "gitea_url" in resp.data
        assert "abstract_tests_ulids" in resp.data

    def test_experiment_hash_to_metadata_combined_hash_not_found(self, api_client):
        exp = ExperimentFactory(published=True)

        resp = api_client.get(_experiment_hash_url(exp.sha256hash))

        assert resp.status_code == 404

    def test_environment_hash_to_metadata(self, api_client):
        env = EnvironmentFactory(published=True)

        resp = api_client.get(_environment_hash_url(env.sha256hash))

        assert resp.status_code == 200
        assert resp.data["ulid"] == env.ulid
        assert resp.data["published"] is True
        assert "gitea_url" in resp.data

    def test_testfunction_hash_to_metadata(self, api_client):
        tfset = TestfunctionSetFactory(published=True)

        resp = api_client.get(_testfunction_hash_url(tfset.sha256hash))

        assert resp.status_code == 200
        assert resp.data["ulid"] == tfset.ulid
        assert resp.data["published"] is True
        assert "gitea_url" in resp.data

    def test_hash_not_found_returns_404(self, api_client):
        fake_hash = hashlib.sha256(b"nonexistent").hexdigest()

        resp = api_client.get(_experiment_hash_url(fake_hash))

        assert resp.status_code == 404

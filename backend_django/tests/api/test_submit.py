import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


SUBMIT_EXPERIMENT_URL = "/api/submit/experiment/"
SUBMIT_TESTFUNCTION_URL = "/api/submit/testfunction/"
SUBMIT_ENVIRONMENT_URL = "/api/submit/environment/"


def _make_file(name="file.txt", content=b"test content"):
    return SimpleUploadedFile(name, content, content_type="text/plain")


@pytest.mark.django_db
class TestSubmitExperiment:
    def test_submit_experiment_returns_fake_pr(self, authenticated_client):
        resp = authenticated_client.post(
            SUBMIT_EXPERIMENT_URL,
            {
                "playbook": _make_file("playbook.yml"),
                "metadata": _make_file("metadata.yml"),
                "name": "my-experiment",
            },
            format="multipart",
        )

        assert resp.status_code == 201
        assert resp.data["pr_url"] == "#dev"
        assert "pr_number" in resp.data


@pytest.mark.django_db
class TestSubmitTestfunction:
    def test_submit_testfunction_returns_fake_pr(self, authenticated_client):
        resp = authenticated_client.post(
            SUBMIT_TESTFUNCTION_URL,
            {
                "testfunction": _make_file("testfunction.py"),
                "requirements": _make_file("requirements.txt"),
                "name": "my-testfunction",
            },
            format="multipart",
        )

        assert resp.status_code == 201
        assert resp.data["pr_url"] == "#dev"
        assert "pr_number" in resp.data


@pytest.mark.django_db
class TestSubmitEnvironment:
    def test_submit_environment_returns_fake_pr(self, authenticated_client):
        resp = authenticated_client.post(
            SUBMIT_ENVIRONMENT_URL,
            {
                "environment": _make_file("environment.yml"),
                "name": "my-environment",
            },
            format="multipart",
        )

        assert resp.status_code == 201
        assert resp.data["pr_url"] == "#dev"
        assert "pr_number" in resp.data


@pytest.mark.django_db
class TestSubmitAuth:
    def test_submit_requires_authentication(self, api_client):
        resp = api_client.post(
            SUBMIT_EXPERIMENT_URL,
            {
                "playbook": _make_file("playbook.yml"),
                "metadata": _make_file("metadata.yml"),
                "name": "my-experiment",
            },
            format="multipart",
        )

        assert resp.status_code == 401


@pytest.mark.django_db
class TestSubmitValidation:
    def test_submit_missing_file_returns_400(self, authenticated_client):
        resp = authenticated_client.post(
            SUBMIT_EXPERIMENT_URL,
            {
                "playbook": _make_file("playbook.yml"),
                # metadata is missing
                "name": "my-experiment",
            },
            format="multipart",
        )

        assert resp.status_code == 400

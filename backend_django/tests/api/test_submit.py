from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from experiments import submit_views
from giteaeventmanager.exception import TaskFailure


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


@pytest.mark.django_db
class TestSubmitInlineIngest:
    """The production submit view opens the PR then ingests it in-process."""

    def _post(self, gitea_user):
        factory = APIRequestFactory()
        request = factory.post(
            SUBMIT_EXPERIMENT_URL,
            {
                "playbook": _make_file("playbook.yml"),
                "metadata": _make_file("metadata.yml"),
                "name": "my-experiment",
            },
            format="multipart",
        )
        force_authenticate(request, user=gitea_user.user)
        return request

    def test_success_returns_201_with_ingest_result(self, gitea_user):
        request = self._post(gitea_user)
        fake_pr = {"html_url": "http://gitea/pr/1", "number": 1}
        fake_ingest = {"experiment_ulid": "01ABC", "tests": [{"name": "t", "type": "IsFile"}]}
        with patch.object(submit_views, "_submit_files", return_value=fake_pr), \
             patch.object(submit_views, "ingest_pr", return_value=fake_ingest) as ing:
            resp = submit_views.SubmitExperimentView.as_view()(request)

        assert resp.status_code == 201
        assert resp.data["pr_number"] == 1
        assert resp.data["ingest"]["experiment_ulid"] == "01ABC"
        ing.assert_called_once_with(1)

    def test_ingest_failure_returns_400_with_error_and_pr(self, gitea_user):
        request = self._post(gitea_user)
        fake_pr = {"html_url": "http://gitea/pr/2", "number": 2}
        with patch.object(submit_views, "_submit_files", return_value=fake_pr), \
             patch.object(submit_views, "ingest_pr", side_effect=TaskFailure("environment nope does not exist")):
            resp = submit_views.SubmitExperimentView.as_view()(request)

        assert resp.status_code == 400
        assert "nope" in resp.data["error"]
        # the PR was still created, so surface it
        assert resp.data["pr_number"] == 2

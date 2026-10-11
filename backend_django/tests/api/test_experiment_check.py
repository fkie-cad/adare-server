import json
import hashlib

import pytest
from django.contrib.contenttypes.models import ContentType

from experiments.models import Experiment
from tests.factories import (
    ExperimentFactory,
    RequestObjectFactory,
)

EXPERIMENT_CHECK_URL = "/api/experiment/check/"
EXPERIMENT_CHECK_MULTIPLE_URL = "/api/experiment/checkmuliple/"


@pytest.mark.django_db
class TestExperimentCheck:
    def test_check_published_by_hash(self, api_client):
        exp = ExperimentFactory(published=True)

        resp = api_client.get(EXPERIMENT_CHECK_URL, {"sha256hash": exp.sha256hash})

        assert resp.status_code == 200
        assert resp.data["published"] is True
        assert resp.data["published_at"] is not None
        assert resp.data["ulid"] == exp.ulid
        assert resp.data["request_ulid"] is None

    def test_check_unpublished_with_request(self, api_client):
        exp = ExperimentFactory(published=False, published_at=None)
        ct = ContentType.objects.get_for_model(Experiment)
        req = RequestObjectFactory(objective=ct, object_id=exp.ulid)

        resp = api_client.get(EXPERIMENT_CHECK_URL, {"sha256hash": exp.sha256hash})

        assert resp.status_code == 200
        assert resp.data["published"] is False
        assert resp.data["published_at"] is None
        assert resp.data["ulid"] == exp.ulid
        assert resp.data["request_ulid"] == req.ulid

    def test_check_nonexistent_hash(self, api_client):
        random_hash = hashlib.sha256(b"nonexistent").hexdigest()

        resp = api_client.get(EXPERIMENT_CHECK_URL, {"sha256hash": random_hash})

        assert resp.status_code == 200
        assert resp.data["published"] is None
        assert resp.data["published_at"] is None
        assert resp.data["ulid"] is None
        assert resp.data["request_ulid"] is None

    def test_check_missing_param_returns_400(self, api_client):
        resp = api_client.get(EXPERIMENT_CHECK_URL)

        assert resp.status_code == 400


@pytest.mark.django_db
class TestExperimentCheckMultiple:
    def test_check_multiple_hashes(self, api_client):
        exp_published = ExperimentFactory(published=True)
        exp_unpublished = ExperimentFactory(published=False, published_at=None)

        hashes = f"{exp_published.sha256hash},{exp_unpublished.sha256hash}"

        # The checkmuliple endpoint reads from request.data, which is
        # unusual for GET.  Use generic() to send a JSON body with GET.
        resp = api_client.generic(
            "GET",
            EXPERIMENT_CHECK_MULTIPLE_URL,
            data=json.dumps({"sha256hashes": hashes}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 2

        # Build a lookup keyed by ulid for order-independent assertions
        by_ulid = {item["ulid"]: item for item in resp.data}

        assert by_ulid[exp_published.ulid]["published"] is True
        assert by_ulid[exp_unpublished.ulid]["published"] is False

    def test_check_multiple_resolves_requests_in_one_query(self, api_client):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        ct = ContentType.objects.get_for_model(Experiment)
        unpublished = ExperimentFactory.create_batch(4, published=False, published_at=None)
        requests = {exp.ulid: RequestObjectFactory(objective=ct, object_id=exp.ulid) for exp in unpublished[:3]}
        hashes = ",".join(exp.sha256hash for exp in unpublished)

        with CaptureQueriesContext(connection) as ctx:
            resp = api_client.generic(
                "GET",
                EXPERIMENT_CHECK_MULTIPLE_URL,
                data=json.dumps({"sha256hashes": hashes}),
                content_type="application/json",
            )

        assert resp.status_code == 200
        by_ulid = {item["ulid"]: item for item in resp.data}
        for exp in unpublished[:3]:
            assert by_ulid[exp.ulid]["request_ulid"] == requests[exp.ulid].ulid
        assert by_ulid[unpublished[3].ulid]["request_ulid"] is None
        request_queries = [q for q in ctx.captured_queries if 'experiments_request' in q['sql']]
        assert len(request_queries) == 1

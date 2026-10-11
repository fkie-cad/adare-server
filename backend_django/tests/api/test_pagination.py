"""List endpoints are always paginated and deterministically ordered."""
from datetime import timedelta

import pytest
from django.utils import timezone

from adare.pagination import DefaultLimitOffsetPagination
from tests.factories import (
    EnvironmentFactory,
    ExperimentFactory,
    ExperimentRunFactory,
    RequestObjectFactory,
    TestfunctionSetFactory,
)

LIST_ENDPOINTS = ['/api/run/', '/api/experiment/', '/api/environment/', '/api/testfunction/', '/api/request/']


@pytest.mark.django_db
class TestDefaultPagination:

    @pytest.mark.parametrize('url', LIST_ENDPOINTS)
    def test_missing_limit_returns_envelope_with_default_page(self, api_client, monkeypatch, url):
        monkeypatch.setattr(DefaultLimitOffsetPagination, 'default_limit', 2)
        for _ in range(3):
            ExperimentRunFactory()
            TestfunctionSetFactory()
            RequestObjectFactory()

        resp = api_client.get(url)

        assert resp.status_code == 200
        assert set(resp.data) == {'count', 'next', 'previous', 'results'}
        assert len(resp.data['results']) == 2
        assert resp.data['next'] is not None

    def test_limit_is_clamped_to_max_limit(self, api_client, monkeypatch):
        monkeypatch.setattr(DefaultLimitOffsetPagination, 'max_limit', 2)
        for _ in range(3):
            ExperimentRunFactory()

        resp = api_client.get('/api/run/', {'limit': 500})

        assert resp.data['count'] == 3
        assert len(resp.data['results']) == 2

    def test_production_defaults(self):
        assert DefaultLimitOffsetPagination.default_limit == 25
        assert DefaultLimitOffsetPagination.max_limit == 200


@pytest.mark.django_db
class TestDefaultOrdering:

    def test_runs_newest_first(self, api_client):
        now = timezone.now()
        old = ExperimentRunFactory(published_at=now - timedelta(days=2))
        new = ExperimentRunFactory(published_at=now)
        mid = ExperimentRunFactory(published_at=now - timedelta(days=1))

        resp = api_client.get('/api/run/')

        assert [r['ulid'] for r in resp.data['results']] == [new.ulid, mid.ulid, old.ulid]

    @pytest.mark.parametrize('factory,url', [
        (ExperimentFactory, '/api/experiment/'),
        (EnvironmentFactory, '/api/environment/'),
    ])
    def test_catalog_lists_newest_first(self, api_client, factory, url):
        now = timezone.now()
        old = factory(published_at=now - timedelta(days=1))
        new = factory(published_at=now)

        resp = api_client.get(url)

        assert [r['ulid'] for r in resp.data['results']] == [new.ulid, old.ulid]

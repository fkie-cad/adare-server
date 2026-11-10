"""INCONCLUSIVE (15) verdict status: seeded row, migration, and ingest acceptance.

A client may now report a run / test result as ``inconclusive``: a negative
test passed but the GUI actions before it could not be proven to take effect.
The server must store it like any other status, not reject it.
"""
import json
from importlib import import_module

import pytest
from django.apps import apps

from experiments.models import ExperimentRun, Status, TestEvent, generate_ulid
from tests.api.test_run_publish import (
    _build_metadata,
    _log_files,
    _make_test_event,
    publish_prerequisites,  # noqa: F401 - pytest fixture
)

_migration = import_module('experiments.migrations.0021_status_inconclusive')


@pytest.mark.django_db
class TestInconclusiveStatusRow:

    def test_fixture_seeds_inconclusive_as_pk_15(self):
        assert Status.objects.get(pk=15).name == 'inconclusive'

    def test_migration_is_idempotent_and_reversible(self):
        _migration.remove_inconclusive(apps, None)
        assert not Status.objects.filter(pk=15).exists()

        from django.db import connection
        with connection.schema_editor() as editor:
            _migration.add_inconclusive(apps, editor)
            _migration.add_inconclusive(apps, editor)

        assert Status.objects.get(pk=15).name == 'inconclusive'
        assert Status.objects.filter(name='inconclusive').count() == 1

    def test_auto_pk_insert_after_migration_does_not_collide(self):
        from django.db import connection
        with connection.schema_editor() as editor:
            _migration.add_inconclusive(apps, editor)

        created = Status.objects.create(name='claude_probe_status')
        assert created.pk > 15


@pytest.mark.django_db
class TestPublishInconclusive:

    def test_run_and_test_result_inconclusive_are_accepted(self, authenticated_client, publish_prerequisites):  # noqa: F811
        p = publish_prerequisites
        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='inconclusive',
            events=[_make_test_event('finished', 'inconclusive', p['abstract_test'].ulid)],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201, response.data
        run = ExperimentRun.objects.get(ulid=metadata['ulid'])
        assert run.result_status.pk == 15
        assert TestEvent.objects.get(run=run).result.status.name == 'inconclusive'

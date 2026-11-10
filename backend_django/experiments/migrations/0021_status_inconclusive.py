"""Seed the INCONCLUSIVE (15) verdict status.

Status rows are otherwise loaded from ``fixtures/status.yaml`` (``loaddata
status``), which a production deploy does not run. This data migration makes
sure row 15 exists everywhere the schema is migrated.

INCONCLUSIVE: a negative test (asserting an artifact is absent) passed, but the
GUI actions it depends on could not be proven to have taken effect. Neither a
pass nor a fail. Run verdict precedence:
FAILED > INCONCLUSIVE > TEST_MISSING > WARNING > SUCCESS.
"""

from django.core.management.color import no_style
from django.db import migrations

INCONCLUSIVE_PK = 15
INCONCLUSIVE_NAME = 'inconclusive'


def _reset_sequence(model, schema_editor):
    # An explicit-pk insert does not advance a Postgres serial sequence; resync
    # it (as loaddata does) so a later auto-pk insert cannot collide with 15.
    for sql in schema_editor.connection.ops.sequence_reset_sql(no_style(), [model]):
        schema_editor.execute(sql)


def add_inconclusive(apps, schema_editor):
    Status = apps.get_model('experiments', 'Status')
    Status.objects.get_or_create(pk=INCONCLUSIVE_PK, defaults={'name': INCONCLUSIVE_NAME})
    _reset_sequence(Status, schema_editor)


def remove_inconclusive(apps, schema_editor):
    Status = apps.get_model('experiments', 'Status')
    Status.objects.filter(pk=INCONCLUSIVE_PK, name=INCONCLUSIVE_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0020_perf_indexes'),
    ]

    operations = [
        migrations.RunPython(add_inconclusive, remove_inconclusive),
    ]

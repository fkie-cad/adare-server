"""Backfill `TestFunction.name` to the qualified `<set>.<name>` identity.

**This is a data-only migration and it is separable from the code fix.** The code
fix (giteaeventmanager/action/plugin.py: qualify_test_name /
qualify_playbook_function) makes *new* testfunction-set ingests store the
qualified name and makes experiment ingest look it up. Rows written before the
fix hold the bare decorator name (`line_matches`), so until they are qualified,
experiment ingest keeps failing with UNKNOWN_DEPENDENCY for every already-
published set. Two ways to get there:

  1. this migration, or
  2. re-ingesting every published testfunction set through a modify PR (which
     creates a new set version and registers it correctly).

If you prefer (2), delete this file before deploying. Nothing in the code depends
on it having run.

Safety
------
`TestFunction` has had `UniqueConstraint(fields=['name', 'testfunction_set'],
name='unique_testfunction')` since 0001_initial, so the table cannot contain two
rows with the same name inside one set. Prefixing every name in a set with that
set's own name is therefore injective *within* the constraint's scope: a
collision is impossible by construction, not by luck. Rows that look duplicated
across set *versions* (same name, different `testfunction_set`) are intended --
each `TestfunctionSet` version owns its own `TestFunction` rows (0015) -- and
each is rewritten with the same prefix, so their distinctness is preserved.
The pre-flight below still counts collisions and aborts rather than trusting
that argument.

Reverse
-------
Best-effort: it strips the `<set>.` prefix again. That is lossy for a name that
was *already* qualified before the forward pass (the shipped `visual` set
declares `name='visual.exists'`, which the forward pass leaves untouched but the
reverse pass would strip to `exists`). Reversing is only sound if you have no
already-qualified rows; check the `already qualified, skipped` log line the
forward pass emits.
"""
import logging

from django.db import migrations

log = logging.getLogger(__name__)


def qualify_names(apps, schema_editor):
    """Rewrite bare `name` values to `<set>.<name>`.

    Idempotent: uses the same rule as plugin.qualify_test_name -- a name that
    already contains a '.' is assumed to carry its set and is left alone -- so a
    second run is a no-op.
    """
    TestFunction = apps.get_model('experiments', 'TestFunction')

    rows = list(TestFunction.objects.select_related('testfunction_set').all())
    pending, skipped = [], []
    for row in rows:
        if '.' in row.name:
            skipped.append(row.name)
            continue
        pending.append((row, f'{row.testfunction_set.name}.{row.name}'))

    # Pre-flight: the unique constraint is (name, testfunction_set), so check that
    # no target name is already taken inside its own set before writing anything.
    # `taken` starts from the rows we are NOT rewriting (the already-qualified
    # ones): a set holding both `line_matches` and `jsonl.line_matches` is the one
    # shape that can actually collide.
    taken = {(row.testfunction_set_id, row.name) for row in rows if '.' in row.name}
    collisions = []
    for row, new_name in pending:
        key = (row.testfunction_set_id, new_name)
        if key in taken:
            collisions.append(key)
        taken.add(key)
    if collisions:
        raise RuntimeError(
            'refusing to qualify TestFunction names: these names are already taken '
            f'in their own set (set_id, name): {sorted(set(collisions))}'
        )

    for row, new_name in pending:
        row.name = new_name
        row.save(update_fields=['name'])

    log.info('qualified %d TestFunction names; %d already qualified, skipped: %s',
             len(pending), len(skipped), sorted(set(skipped)))


def unqualify_names(apps, schema_editor):
    """Best-effort reverse: strip a leading `<set>.` (see the module docstring)."""
    TestFunction = apps.get_model('experiments', 'TestFunction')

    for row in TestFunction.objects.select_related('testfunction_set').all():
        prefix = f'{row.testfunction_set.name}.'
        if not row.name.startswith(prefix):
            continue
        stripped = row.name[len(prefix):]
        if not stripped:
            log.warning('not stripping %r: nothing would be left of the name', row.name)
            continue
        row.name = stripped
        row.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        # NOT 0017_environment_source_profile_source_iso_sha256: that migration
        # belongs to an unrelated, separately-reviewed provenance feature and is
        # deliberately not part of this deploy. Depend on the last migration that
        # actually ships with this change. If 0017 lands later, its own migration
        # will need to declare a dependency on this one (0018) rather than the
        # other way around, since this is the one being deployed first.
        ('experiments', '0016_recipe_iso_name_recipe_iso_notes_recipe_provision_and_more'),
    ]

    operations = [
        migrations.RunPython(qualify_names, unqualify_names),
    ]

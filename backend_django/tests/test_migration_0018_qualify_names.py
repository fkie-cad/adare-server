"""Tests for the optional 0018 backfill that qualifies TestFunction names.

The migration functions are called directly against the live apps registry: 0018
is data-only and does not change the model shape, so the historical and current
models are identical here.
"""
from importlib import import_module

import pytest
from django.apps import apps

from experiments.models import TestFunction
from tests.factories import TestFunctionFactory, TestfunctionSetFactory

_migration = import_module('experiments.migrations.0018_qualify_testfunction_names')
qualify_names = _migration.qualify_names
unqualify_names = _migration.unqualify_names


@pytest.mark.django_db
class TestQualifyNamesBackfill:

    def test_bare_names_get_their_set_prefix(self):
        jsonl = TestfunctionSetFactory(name='jsonl')
        TestFunctionFactory(name='line_matches', testfunction_set=jsonl)

        qualify_names(apps, None)

        assert list(jsonl.testfunctions.values_list('name', flat=True)) == ['jsonl.line_matches']

    def test_same_bare_name_in_two_sets_becomes_two_distinct_names(self):
        csv = TestfunctionSetFactory(name='csv')
        excel = TestfunctionSetFactory(name='excel')
        TestFunctionFactory(name='compare_rows', testfunction_set=csv)
        TestFunctionFactory(name='compare_rows', testfunction_set=excel)

        qualify_names(apps, None)

        assert csv.testfunctions.get().name == 'csv.compare_rows'
        assert excel.testfunctions.get().name == 'excel.compare_rows'

    def test_already_qualified_names_are_left_alone(self):
        visual = TestfunctionSetFactory(name='visual')
        TestFunctionFactory(name='visual.exists', testfunction_set=visual)

        qualify_names(apps, None)

        assert visual.testfunctions.get().name == 'visual.exists'

    def test_is_idempotent(self):
        jsonl = TestfunctionSetFactory(name='jsonl')
        TestFunctionFactory(name='line_matches', testfunction_set=jsonl)

        qualify_names(apps, None)
        qualify_names(apps, None)

        assert list(jsonl.testfunctions.values_list('name', flat=True)) == ['jsonl.line_matches']

    def test_per_version_rows_are_all_rewritten_and_stay_distinct(self):
        """Same name across set versions is intended (0015), not a duplicate."""
        v1 = TestfunctionSetFactory(name='jsonl', version=1, is_current=False)
        v2 = TestfunctionSetFactory(name='jsonl', version=2, is_current=True)
        TestFunctionFactory(name='line_matches', testfunction_set=v1)
        TestFunctionFactory(name='line_matches', testfunction_set=v2)

        qualify_names(apps, None)

        assert v1.testfunctions.get().name == 'jsonl.line_matches'
        assert v2.testfunctions.get().name == 'jsonl.line_matches'
        assert TestFunction.objects.filter(name='jsonl.line_matches').count() == 2

    def test_aborts_instead_of_colliding_with_an_already_qualified_row(self):
        jsonl = TestfunctionSetFactory(name='jsonl')
        TestFunctionFactory(name='line_matches', testfunction_set=jsonl)
        TestFunctionFactory(name='jsonl.line_matches', testfunction_set=jsonl)

        with pytest.raises(RuntimeError, match='already taken'):
            qualify_names(apps, None)

        # nothing was written
        assert set(jsonl.testfunctions.values_list('name', flat=True)) == {
            'line_matches', 'jsonl.line_matches'}

    def test_reverse_strips_the_prefix(self):
        jsonl = TestfunctionSetFactory(name='jsonl')
        TestFunctionFactory(name='line_matches', testfunction_set=jsonl)

        qualify_names(apps, None)
        unqualify_names(apps, None)

        assert jsonl.testfunctions.get().name == 'line_matches'

    def test_reverse_is_lossy_for_names_that_were_already_qualified(self):
        """Documented limitation, asserted so it cannot surprise anyone."""
        visual = TestfunctionSetFactory(name='visual')
        TestFunctionFactory(name='visual.exists', testfunction_set=visual)

        qualify_names(apps, None)
        unqualify_names(apps, None)

        assert visual.testfunctions.get().name == 'exists'  # NOT 'visual.exists'

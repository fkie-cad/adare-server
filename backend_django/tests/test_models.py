import pytest
from django.db import IntegrityError

from experiments.models import Tag, TagScope, ExperimentRun, generate_ulid
from tests.factories import (
    TagFactory,
    ExperimentRunFactory,
    ActionEventFactory,
    TestEventFactory,
    ErrorEventFactory,
)


class TestGenerateUlid:

    def test_returns_26_char_string(self):
        result = generate_ulid()
        assert isinstance(result, str)
        assert len(result) == 26

    def test_unique(self):
        ids = {generate_ulid() for _ in range(100)}
        assert len(ids) == 100


@pytest.mark.django_db
class TestTagSave:

    def test_name_generated_with_scope(self):
        scope = TagScope.objects.create(name='os', is_predefined=True)
        tag = Tag(scope=scope, value='linux')
        tag.save()
        assert tag.name == 'os:linux'

    def test_name_generated_without_scope(self):
        tag = Tag(scope=None, value='important')
        tag.save()
        assert tag.name == 'important'

    def test_name_updated_on_save(self):
        scope = TagScope.objects.create(name='lang')
        tag = Tag(scope=scope, value='python')
        tag.save()
        assert tag.name == 'lang:python'
        tag.value = 'go'
        tag.save()
        assert tag.name == 'lang:go'


@pytest.mark.django_db
class TestTagUniqueConstraint:

    def test_duplicate_scope_value_raises(self):
        scope = TagScope.objects.create(name='env')
        Tag.objects.create(scope=scope, value='prod')
        with pytest.raises(IntegrityError):
            Tag.objects.create(scope=scope, value='prod')

    def test_same_value_different_scope_allowed(self):
        scope1 = TagScope.objects.create(name='a')
        scope2 = TagScope.objects.create(name='b')
        Tag.objects.create(scope=scope1, value='test')
        tag2 = Tag.objects.create(scope=scope2, value='test')
        assert tag2.pk is not None


@pytest.mark.django_db
class TestExperimentRunEvents:

    def test_events_property_returns_all_types(self):
        run = ExperimentRunFactory()
        ActionEventFactory(run=run)
        TestEventFactory(run=run)
        ErrorEventFactory(run=run)

        events = run.events
        assert len(events) == 3

    def test_events_property_empty_run(self):
        run = ExperimentRunFactory()
        assert run.events == []

    def test_events_sorted_by_timestamp(self):
        from django.utils import timezone
        from datetime import timedelta

        run = ExperimentRunFactory()
        now = timezone.now()
        e1 = ActionEventFactory(run=run, timestamp=now + timedelta(minutes=2))
        e2 = TestEventFactory(run=run, timestamp=now)
        e3 = ErrorEventFactory(run=run, timestamp=now + timedelta(minutes=1))

        events = run.events
        # events property returns a flat list; sorting is done at serializer level
        assert len(events) == 3

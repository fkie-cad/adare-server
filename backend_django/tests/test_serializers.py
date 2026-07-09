import pytest

from experiments.serializers import (
    get_event_serializer,
    ActionEventSerializer,
    TestEventSerializer,
    ErrorEventSerializer,
    GenericRequestObjectSerializer,
    ResultSerializer,
)
from experiments.models import TestEvent, ErrorEvent, ActionEvent, Status, Result
from tests.factories import (
    TestEventFactory,
    ErrorEventFactory,
    ActionEventFactory,
    ExperimentFactory,
    EnvironmentFactory,
    TestfunctionSetFactory,
    StatusFactory,
)


class TestGetEventSerializerByCategory:

    def test_command_returns_action_serializer(self):
        assert get_event_serializer('command') is ActionEventSerializer

    def test_action_returns_action_serializer(self):
        assert get_event_serializer('action') is ActionEventSerializer

    def test_test_returns_test_serializer(self):
        assert get_event_serializer('test') is TestEventSerializer

    def test_error_returns_error_serializer(self):
        assert get_event_serializer('error') is ErrorEventSerializer

    def test_unknown_category_raises(self):
        with pytest.raises(ValueError, match='Unknown category'):
            get_event_serializer('nonexistent')


@pytest.mark.django_db
class TestGetEventSerializerByInstance:

    def test_action_event_instance(self):
        event = ActionEventFactory()
        assert get_event_serializer(event) is ActionEventSerializer

    def test_test_event_instance(self):
        event = TestEventFactory()
        assert get_event_serializer(event) is TestEventSerializer

    def test_error_event_instance(self):
        event = ErrorEventFactory()
        assert get_event_serializer(event) is ErrorEventSerializer


@pytest.mark.django_db
class TestResultSerializerCreate:

    def test_create_with_string_status(self):
        StatusFactory(name='success')
        serializer = ResultSerializer(data={'details': 'passed', 'status': 'success'})
        # ResultSerializer has status as read_only, so we test create() directly
        result = ResultSerializer().create({'details': 'passed', 'status': 'success'})
        assert result.pk is not None
        assert result.status.name == 'success'
        assert result.details == 'passed'

    def test_create_with_int_status(self):
        status = StatusFactory(name='failed')
        result = ResultSerializer().create({'details': 'error', 'status': status.id})
        assert result.status.name == 'failed'

    def test_create_with_unknown_status_raises(self):
        with pytest.raises(Exception):
            ResultSerializer().create({'details': '', 'status': 'nonexistent'})


@pytest.mark.django_db
class TestGenericRequestObjectSerializer:

    def test_experiment_representation(self):
        exp = ExperimentFactory()
        field = GenericRequestObjectSerializer()
        data = field.to_representation(exp)
        assert data['ulid'] == exp.ulid
        assert data['name'] == exp.name

    def test_environment_representation(self):
        env = EnvironmentFactory()
        field = GenericRequestObjectSerializer()
        data = field.to_representation(env)
        assert data['name'] == env.name

    def test_testfunctionset_representation(self):
        tfs = TestfunctionSetFactory()
        field = GenericRequestObjectSerializer()
        data = field.to_representation(tfs)
        assert data['name'] == tfs.name

    def test_none_returns_none(self):
        field = GenericRequestObjectSerializer()
        assert field.to_representation(None) is None

    def test_unknown_type_raises(self):
        field = GenericRequestObjectSerializer()
        with pytest.raises(Exception, match='Unexpected type'):
            field.to_representation(object())

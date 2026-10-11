from rest_framework import serializers

from django.contrib.auth.models import User
from users.serializers import GiteaUserSerializer
from helperfunctions.gitea import convert_gitea_internal_api_url_to_viewable_url, convert_gitea_internal_api_url_to_external
from helperfunctions.minio import get_presigned_url

from experiments.models import (
    Tag, TagScope, Status, Result, TestParameter, TestParameterEntry, Event,
    TestEvent, ErrorEvent, ActionEvent, Requirement, TestfunctionSet,
    TestFunction, Tool, AbstractTest, OsInfo, PostSetupInstallation, Recipe,
    Environment, Experiment, ExperimentRun, Label, Request,
)

class ExternalDownloadURLMixin:
    """Rewrites the listed fields from Gitea's internal raw-API URL to the externally
    reachable one. Centralized here so every download-serving serializer goes through
    convert_gitea_internal_api_url_to_external and can't drift onto the HTML blob-view
    URL (convert_gitea_internal_api_url_to_viewable_url) by mistake, as Environment and
    TestFunctionSet previously did.
    """
    external_url_fields = []

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for field in self.external_url_fields:
            if ret.get(field):
                ret[field] = convert_gitea_internal_api_url_to_external(ret[field])
        return ret


class TagScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagScope
        fields = ['name', 'is_predefined', 'color']


class TagSerializer(serializers.ModelSerializer):
    scope = serializers.CharField(source='scope.name', read_only=True, allow_null=True, default=None)
    color = serializers.CharField(source='scope.color', read_only=True, allow_null=True, default=None)

    class Meta:
        model = Tag
        fields = [
            'name',
            'scope',
            'value',
            'color',
        ]


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = [
            'name',
            'color',
            'description',
        ]


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = [
            'name',
        ]


class PostSetupInstallationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostSetupInstallation
        fields = [
            'name',
            'description',
            'command',
            'shell',
            'cwd',
        ]
        extra_kwargs = {
            'shell': {'required': False},
            'cwd': {'required': False},
        }


class OsInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OsInfo
        fields = [
            'platform',
            'os',
            'distribution',
            'version',
            'language',
            'architecture',
            'details',
        ]
        extra_kwargs = {
            'platform': {'required': False},
            'version': {'required': False},
            'language': {'required': False},
            'architecture': {'required': False},
            'details': {'required': False},
        }


class RecipeSerializer(serializers.ModelSerializer):
    """Describes a recipe environment as published.

    `iso_name`/`iso_notes`/`provision` are part of the API surface on purpose:
    without them a BYO recipe would look like it has no ISO at all, and a
    heavily provisioned tutorial environment would be described as a bare OS
    install. `iso_notes` is publisher-supplied plain text -- consumers must
    render it as text, never as markdown/HTML (see the Recipe model comment).
    """
    class Meta:
        model = Recipe
        fields = [
            'profile',
            'iso',
            'iso_name',
            'iso_notes',
            'iso_sha256',
            'template',
            'setup_level',
            'disk_size',
            'ram_mb',
            'cpus',
            'arch',
            'provision',
        ]


class EnvironmentMetadataSerializer(serializers.ModelSerializer):
    gitea_url = serializers.SerializerMethodField('get_gitea_url', read_only=True)

    class Meta:
        model = Environment
        fields = [
            'ulid',
            'gitea_url',
            'published',
        ]

    def get_gitea_url(self, obj):
        environment_url_gitea = obj.file
        environment_url_gitea = convert_gitea_internal_api_url_to_viewable_url(environment_url_gitea)
        return environment_url_gitea


class EnvironmentSerializer(ExternalDownloadURLMixin, serializers.ModelSerializer):
    os_info = OsInfoSerializer()
    recipe = RecipeSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    post_setup_installations = PostSetupInstallationSerializer(many=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True, allow_null=True, default=None)
    external_url_fields = ['file']

    class Meta:
        model = Environment
        fields = [
            'name',
            'ulid',
            'vm',
            'vm_sha256',
            'source_profile',
            'source_iso_sha256',
            'vagrantbox',
            'vagrantbox_cloud_url',
            'recipe',
            'description',
            'os_info',
            'tags',
            'file',
            'sha256hash',
            'post_setup_installations',
            'published',
            'published_at',
            'published_by',
            'created_by',
        ]


class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = [
            'name',
            'command',
        ]


class ResultSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = Result
        fields = [
            'details',
            'status'
        ]

    def create(self, validated_data):
        status_key = validated_data.pop('status')
        # Look up status by name (string) or primary key (int)
        try:
            if isinstance(status_key, str):
                status = Status.objects.get(name=status_key)
            else:
                status = Status.objects.get(id=status_key)
        except Status.DoesNotExist:
            raise serializers.ValidationError(f'Status "{status_key}" not found')
        validated_data['status'] = status
        result = Result.objects.create(**validated_data)
        return result


class TestParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestParameter
        fields = [
            'name',
            'dtype',
            'description',
        ]
        extra_kwargs = {
            'name': {
                'validators': [],
            },
        }


class TestParameterEntrySerializer(serializers.ModelSerializer):
    parameter = TestParameterSerializer()

    class Meta:
        model = TestParameterEntry
        fields = [
            'parameter',
            'value',
        ]


class TestFunctionSerializer(serializers.ModelSerializer):
    possible_parameters = TestParameterSerializer(many=True)
    set = serializers.CharField(source='testfunction_set.name', read_only=True)

    class Meta:
        model = TestFunction
        fields = [
            'name',
            'description',
            'possible_parameters',
            'set',
        ]
        extra_kwargs = {
            'description': {'required': False},
            'name': {
                'validators': [],
            },
        }


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = [
            'package',
            'version',
            'relation',
        ]


class TestFunctionSetMetadataSerializer(serializers.ModelSerializer):
    gitea_url = serializers.SerializerMethodField('get_gitea_url', read_only=True)

    class Meta:
        model = TestfunctionSet
        fields = [
            'ulid',
            'gitea_url',
            'published',
            'version',
            'is_current',
        ]

    def get_gitea_url(self, obj):
        testfunctionset_url_gitea = obj.file
        # take parent directory
        testfunctionset_url_gitea = '/'.join(testfunctionset_url_gitea.split('/')[:-1])
        testfunctionset_url_gitea = convert_gitea_internal_api_url_to_viewable_url(testfunctionset_url_gitea)
        return testfunctionset_url_gitea


class TestFunctionSetSerializer(ExternalDownloadURLMixin, serializers.ModelSerializer):
    requirements = RequirementSerializer(many=True)
    tags = TagSerializer(many=True, read_only=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    testfunctions = TestFunctionSerializer(many=True)
    external_url_fields = ['file', 'requirements_file']

    class Meta:
        model = TestfunctionSet
        fields = [
            'name',
            'description',
            'testfunctions',
            'num_testfunctions',
            'tags',
            'file',
            'requirements_file',
            'requirements',
            'sha256hash',
            'sha256testfunctionset',
            'sha256requirements',
            'published_by',
            'created_by',
            'published_at',
            'published',
            'version',
            'is_current',
        ]


class AbstractTestSerializer(serializers.ModelSerializer):
    testfunction = TestFunctionSerializer()
    parameters = TestParameterEntrySerializer(many=True)
    tools = ToolSerializer(many=True, required=False)

    class Meta:
        model = AbstractTest
        fields = [
            'ulid',
            'name',
            'description',
            'repetitions',
            'testfunction',
            'parameters',
            'tools',
        ]
        extra_kwargs = {
            'repetitions': {'required': False},
        }


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class ExperimentMetadataSerializer(serializers.ModelSerializer):
    gitea_url = serializers.SerializerMethodField('get_gitea_url', read_only=True)
    abstract_tests_ulids = serializers.SerializerMethodField('get_abstract_tests_ulids', read_only=True)

    class Meta:
        model = Experiment
        fields = [
            'ulid',
            'gitea_url',
            'abstract_tests_ulids',
            'published',
        ]

    def get_gitea_url(self, obj):
        experiment_url_gitea = obj.playbook_file
        # take parent directory
        experiment_url_gitea = '/'.join(experiment_url_gitea.split('/')[:-1])
        experiment_url_gitea = convert_gitea_internal_api_url_to_viewable_url(experiment_url_gitea)
        return experiment_url_gitea

    def get_abstract_tests_ulids(self, obj):
        return {
            abstract_test.name: abstract_test.ulid for abstract_test in obj.abstract_tests.all()
        }


class ExperimentSerializer(ExternalDownloadURLMixin, serializers.ModelSerializer):
    run_counts = serializers.SerializerMethodField('get_run_counts', read_only=True)
    abstract_tests = AbstractTestSerializer(read_only=True, many=True)
    tags = TagSerializer(many=True, read_only=True)
    environments = EnvironmentSerializer(read_only=True, many=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    external_url_fields = ['playbook_file', 'metadata_file']

    class Meta:
        model = Experiment
        fields = [
            'ulid',
            'name',
            'description',

            'playbook_file',
            'metadata_file',

            'environments',
            'abstract_tests',
            'tags',

            'sha256hash',
            'sha256playbook',

            'published',
            'published_by',
            'created_by',
            'published_at',

            'run_counts',
        ]
        extra_kwargs = {
            'tags': {'read_only': True},
            'abstract_tests': {'read_only': True},
        }

    def get_run_counts(self, obj):
        # Use annotated fields from the view queryset if available
        successful = getattr(obj, 'successful_run_count', None)
        failed = getattr(obj, 'failed_run_count', None)
        if successful is not None and failed is not None:
            return {
                'successful': successful,
                'failed': failed,
            }
        # Fallback for non-annotated querysets (e.g. detail views)
        successful = obj.experiment_runs.filter(result_status__name='success').count()
        failed = obj.experiment_runs.filter(result_status__name='failed').count()
        return {
            'successful': successful,
            'failed': failed,
        }


class ExperimentViewableFilesSerializer(ExperimentSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['playbook_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.playbook_file)
        ret['metadata_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.metadata_file)
        return ret


def _convert_to_presigned_url(url):
    if url:
        try:
            return get_presigned_url(url)
        except Exception:
            return None
    return None

class ExperimentRunSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)
    result_status = StatusSerializer(read_only=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    experiment = serializers.CharField(source='experiment.name', read_only=True)
    environment = serializers.CharField(source='environment.name', read_only=True)
    events = serializers.SerializerMethodField('get_events', read_only=True)
    duration = serializers.SerializerMethodField('get_duration', read_only=True)
    adarevm_logfile = serializers.SerializerMethodField('get_adarevm_logfile', read_only=True)
    installations_logfile = serializers.SerializerMethodField('get_installations_logfile', read_only=True)
    packagedump_logfile = serializers.SerializerMethodField('get_packagedump_logfile', read_only=True)
    networkdrives_logfile = serializers.SerializerMethodField('get_networkdrives_logfile', read_only=True)

    def get_adarevm_logfile(self, obj):
        return _convert_to_presigned_url(obj.adarevm_logfile.name if obj.adarevm_logfile else None)

    def get_installations_logfile(self, obj):
        return _convert_to_presigned_url(obj.installations_logfile.name if obj.installations_logfile else None)

    def get_packagedump_logfile(self, obj):
        return _convert_to_presigned_url(obj.packagedump_logfile.name if obj.packagedump_logfile else None)

    def get_networkdrives_logfile(self, obj):
        return _convert_to_presigned_url(obj.networkdrives_logfile.name if obj.networkdrives_logfile else None)

    def get_events(self, obj):
        from django.utils.dateparse import parse_datetime

        def _duration_seconds(ts1, ts2):
            dt1 = parse_datetime(ts1) if isinstance(ts1, str) else ts1
            dt2 = parse_datetime(ts2) if isinstance(ts2, str) else ts2
            if dt1 and dt2:
                return (dt2 - dt1).total_seconds()
            return -1

        event_deserialized = []
        for event in sorted(obj.events, key=lambda e: e.timestamp):
            event_serializer = get_event_serializer(event)(event)
            event_deserialized.append(event_serializer.data)

        # Group events by event_group_id, collapsing start/complete pairs
        filtered_events = {}
        for event in event_deserialized:
            group_id = event.get('event_group_id', '')
            if not group_id:
                # No group — standalone event
                event['duration'] = event.get('execution_time') or -1
                filtered_events[event['ulid']] = event
            elif group_id not in filtered_events:
                event['duration'] = event.get('execution_time') or -1
                filtered_events[group_id] = event
            else:
                # Second event in group — compute duration from timestamps
                if event['status']['name'] == 'finished':
                    duration = _duration_seconds(filtered_events[group_id]['timestamp'], event['timestamp'])
                    event['duration'] = duration
                    filtered_events[group_id] = event
                else:
                    duration = _duration_seconds(event['timestamp'], filtered_events[group_id]['timestamp'])
                    filtered_events[group_id]['duration'] = duration
        return list(filtered_events.values())

    def get_duration(self, obj):
        if obj.timestamp_start and obj.timestamp_end:
            return (obj.timestamp_end - obj.timestamp_start).total_seconds()
        return None


    class Meta:
        model = ExperimentRun
        fields = [
            'ulid',
            'run_number',
            'published_by',
            'published_at',
            'timestamp_start',
            'timestamp_end',
            'events',
            'status',
            'result_status',
            'experiment',
            'environment',
            'duration',
            'adarevm_logfile',
            'installations_logfile',
            'packagedump_logfile',
            'networkdrives_logfile',
        ]


class ExperimentRunListSerializer(ExperimentRunSerializer):
    """Run list rows: everything but `events`.

    The full event timeline is only rendered on the run detail page
    (`/api/run/run_<ulid>/`); serializing it for every row of the list made
    the list cost grow with runs x events.
    """
    class Meta(ExperimentRunSerializer.Meta):
        fields = [f for f in ExperimentRunSerializer.Meta.fields if f != 'events']


class GenericRequestObjectSerializer(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, Experiment):
            return ExperimentSerializer(value).data
        elif isinstance(value, TestfunctionSet):
            return TestFunctionSetSerializer(value).data
        elif isinstance(value, Environment):
            return EnvironmentSerializer(value).data
        else:
            raise Exception('Unexpected type of request object')


class RequestSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    last_change_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    object = GenericRequestObjectSerializer(read_only=True)
    requester = GiteaUserSerializer(read_only=True)
    reviewers = GiteaUserSerializer(read_only=True, many=True)
    assignees = GiteaUserSerializer(read_only=True, many=True)

    labels = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = Request
        fields = [
            'title',
            'ulid',
            'description',

            'creation_date',
            'last_change_date',

            'gitea_pr_url',
            'gitea_pr_number',
            'gitea_pr_status',
            'action',
            'object',
            'objective_name',

            'requester',
            'reviewers',
            'assignees',
            'labels',
        ]


class ExperimentRunCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentRun
        fields = [
            'ulid',
            'published_by',
            'published_at',
            'timestamp_start',
            'timestamp_end',
            'experiment',
            'environment',
            'status',
            'result_status',
            'content_hash',
            'adarevm_logfile',
            'installations_logfile',
            'packagedump_logfile',
            'networkdrives_logfile',
        ]
        extra_kwargs = {
            'experiment': {'validators': []},
            'installations_logfile': {'required': False},
            'packagedump_logfile': {'required': False},
            'adarevm_logfile': {'required': False},
            'networkdrives_logfile': {'required': False},
            'content_hash': {'required': False},
        }


class _EventSerializerMixin:
    """Shared create logic for resolving run and status from validated_data."""

    def _resolve_run_and_status(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            validated_data['run'] = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise serializers.ValidationError('Run not found')

        status_name = validated_data.pop('status')
        try:
            validated_data['status'] = Status.objects.get(name=status_name)
        except Status.DoesNotExist:
            raise serializers.ValidationError(f'Status "{status_name}" not found')


class ActionEventSerializer(_EventSerializerMixin, serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = ActionEvent
        fields = [
            'ulid',
            'category',
            'status',
            'error',
            'timestamp',
            'success',
            'event_group_id',
            'event_type_specific',
            'execution_time',
            'action_type',
            'action_id',
            'action_data',
        ]

    def create(self, validated_data):
        self._resolve_run_and_status(validated_data)
        return ActionEvent.objects.create(**validated_data)


class TestEventSerializer(_EventSerializerMixin, serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)
    result = ResultSerializer(read_only=True)
    abstracttest = AbstractTestSerializer(read_only=True)

    class Meta:
        model = TestEvent
        fields = [
            'ulid',
            'category',
            'status',
            'error',
            'timestamp',
            'success',
            'event_group_id',
            'event_type_specific',
            'execution_time',
            'result',
            'abstracttest',
        ]

    def create(self, validated_data):
        result_data = validated_data.pop('result', None)
        if result_data:
            try:
                result_status = Status.objects.get(name=result_data['status'])
            except Status.DoesNotExist:
                raise serializers.ValidationError(f'Result status "{result_data["status"]}" not found')
            try:
                result = Result.objects.get(status=result_status, details=result_data.get('details', ''))
            except Result.DoesNotExist:
                result = Result.objects.create(status=result_status, details=result_data.get('details', ''))
            validated_data['result'] = result

        abstracttest_ulid = validated_data.pop('abstracttest')
        try:
            abstracttest = AbstractTest.objects.get(ulid=abstracttest_ulid)
        except AbstractTest.DoesNotExist:
            raise serializers.ValidationError(f'AbstractTest "{abstracttest_ulid}" not found')
        validated_data['abstracttest'] = abstracttest

        self._resolve_run_and_status(validated_data)
        return TestEvent.objects.create(**validated_data)


class ErrorEventSerializer(_EventSerializerMixin, serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = ErrorEvent
        fields = [
            'ulid',
            'category',
            'status',
            'error',
            'timestamp',
            'success',
            'event_group_id',
            'event_type_specific',
            'execution_time',
            'error_name',
            'error_msg',
        ]

    def create(self, validated_data):
        self._resolve_run_and_status(validated_data)
        return ErrorEvent.objects.create(**validated_data)


_CATEGORY_SERIALIZER_MAP = {
    'command': ActionEventSerializer,
    'action': ActionEventSerializer,
    'test': TestEventSerializer,
    'error': ErrorEventSerializer,
}


def get_event_serializer(event):
    """Dual-mode: pass a category string or a model instance."""
    if isinstance(event, str):
        serializer = _CATEGORY_SERIALIZER_MAP.get(event)
        if not serializer:
            raise ValueError(f'Unknown category: {event}')
        return serializer
    if isinstance(event, TestEvent):
        return TestEventSerializer
    if isinstance(event, ErrorEvent):
        return ErrorEventSerializer
    if isinstance(event, ActionEvent):
        return ActionEventSerializer
    raise ValueError(f'Unknown event: {type(event).__name__}')

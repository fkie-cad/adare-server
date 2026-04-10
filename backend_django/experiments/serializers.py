from rest_framework import serializers

from django.contrib.auth.models import User
from users.serializers import GiteaUserSerializer
from helperfunctions.gitea import convert_gitea_internal_api_url_to_viewable_url, convert_gitea_internal_api_url_to_external
from helperfunctions.minio import get_presigned_url

from experiments.models import (
    Tag, TagScope, Status, Result, TestParameter, TestParameterEntry, Event,
    CommandEvent, TestEvent, ErrorEvent, GuiFindEvent, GuiClickEvent,
    GuiKeypressEvent, GuiIdleEvent, Requirement, TestfunctionSet,
    TestFunction, Tool, AbstractTest, OsInfo, PostSetupInstallation,
    Environment, Experiment, ExperimentRun, Label, Request,
    RequestCreationMessage,
)

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
        ]


class OsInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OsInfo
        fields = [
            'os',
            'distribution',
            'version',
            'language',
            'architecture',
            'details',
        ]
        extra_kwargs = {
            'version': {'required': False},
            'language': {'required': False},
            'architecture': {'required': False},
            'details': {'required': False},
        }


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


class EnvironmentSerializer(serializers.ModelSerializer):
    os_info = OsInfoSerializer()
    tags = TagSerializer(many=True, read_only=True)
    post_setup_installations = PostSetupInstallationSerializer(many=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True, allow_null=True, default=None)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['file']:
            ret['file'] = convert_gitea_internal_api_url_to_viewable_url(ret['file'])
        return ret

    class Meta:
        model = Environment
        fields = [
            'name',
            'ulid',
            'vagrantbox',
            'vagrantbox_cloud_url',
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
        # get status by primary key
        try:
            status = Status.objects.get(id=status_key)
        except Status.DoesNotExist:
            raise Exception('Status not found')
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
        ]

    def get_gitea_url(self, obj):
        testfunctionset_url_gitea = obj.file
        # take parent directory
        testfunctionset_url_gitea = '/'.join(testfunctionset_url_gitea.split('/')[:-1])
        testfunctionset_url_gitea = convert_gitea_internal_api_url_to_viewable_url(testfunctionset_url_gitea)
        return testfunctionset_url_gitea


class TestFunctionSetSerializer(serializers.ModelSerializer):
    requirements = RequirementSerializer(many=True)
    tags = TagSerializer(many=True, read_only=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    testfunctions = TestFunctionSerializer(many=True)

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
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['file']:
            ret['file'] = convert_gitea_internal_api_url_to_viewable_url(ret['file'])
        if 'requirements_file' in ret.keys() and ret['requirements_file'] != '':
            ret['requirements_file'] = convert_gitea_internal_api_url_to_viewable_url(ret['requirements_file'])
        return ret


class AbstractTestSerializer(serializers.ModelSerializer):
    testfunction = TestFunctionSerializer()
    parameters = TestParameterEntrySerializer(many=True)
    tool = ToolSerializer(required=False, allow_null=True)

    class Meta:
        model = AbstractTest
        fields = [
            'ulid',
            'name',
            'description',
            'testfunction',
            'parameters',
            'tool',
        ]


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
        experiment_url_gitea = obj.action_file
        # take parent directory
        experiment_url_gitea = '/'.join(experiment_url_gitea.split('/')[:-1])
        experiment_url_gitea = convert_gitea_internal_api_url_to_viewable_url(experiment_url_gitea)
        return experiment_url_gitea

    def get_abstract_tests_ulids(self, obj):
        return {
            abstract_test.name: abstract_test.ulid for abstract_test in obj.abstract_tests.all()
        }


class ExperimentSerializer(serializers.ModelSerializer):
    run_counts = serializers.SerializerMethodField('get_run_counts', read_only=True)
    abstract_tests = AbstractTestSerializer(read_only=True, many=True)
    tags = TagSerializer(many=True, read_only=True)
    environments = EnvironmentSerializer(read_only=True, many=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Experiment
        fields = [
            'ulid',
            'name',
            'description',

            'action_file',
            'testset_file',
            'metadata_file',

            'environments',
            'abstract_tests',
            'tags',

            'sha256hash',
            'sha256action',
            'sha256testset',

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['action_file']:
            ret['action_file'] = convert_gitea_internal_api_url_to_external(ret['action_file'])
        if ret['testset_file']:
            ret['testset_file'] = convert_gitea_internal_api_url_to_external(ret['testset_file'])
        if ret['metadata_file']:
            ret['metadata_file'] = convert_gitea_internal_api_url_to_external(ret['metadata_file'])
        return ret

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
        ret['action_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.action_file)
        ret['testset_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.testset_file)
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
        return _convert_to_presigned_url(obj.adarevm_logfile.name)

    def get_installations_logfile(self, obj):
        return _convert_to_presigned_url(obj.installations_logfile.name)

    def get_packagedump_logfile(self, obj):
        return _convert_to_presigned_url(obj.packagedump_logfile.name)

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

        filtered_events = {}
        for event in event_deserialized:
            if event['group_id'] not in filtered_events:
                event['duration'] = -1
                filtered_events[event['group_id']] = event
            else:
                if event['status']['name'] == 'finished':
                    duration = _duration_seconds(filtered_events[event['group_id']]['timestamp'], event['timestamp'])
                    event['duration'] = duration
                    filtered_events[event['group_id']] = event
                else:
                    duration = _duration_seconds(event['timestamp'], filtered_events[event['group_id']]['timestamp'])
                    filtered_events[event['group_id']]['duration'] = duration
        return list(filtered_events.values())

    def get_duration(self, obj):
        if obj.timestamp_start and obj.timestamp_end:
            return (obj.timestamp_end - obj.timestamp_start).total_seconds()
        return None


    class Meta:
        model = ExperimentRun
        fields = [
            'ulid',
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
            'experiment',
            'adarevm_logfile',
            'installations_logfile',
            'packagedump_logfile',
            'networkdrives_logfile',
        ]
        extra_kwargs = {
            'experiment': {'validators': []},
        }

class CommandEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = CommandEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'name',
            'command',
            'returncode',
            'stdout',
        ]

    def create(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        command_event = CommandEvent.objects.create(**validated_data)
        return command_event

class TestEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)
    result = ResultSerializer(read_only=True)
    abstracttest = AbstractTestSerializer(read_only=True)

    class Meta:
        model = TestEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'result',
            'abstracttest',
        ]

    def create(self, validated_data):
        result_data = validated_data.pop('result')
        # check if dict is empty
        if result_data:
            try:
                try:
                    status = Status.objects.get(id=result_data['status'])
                except Status.DoesNotExist:
                    raise Exception('Status not found')
                result = Result.objects.get(status=status, details=result_data['details'])
            except Result.DoesNotExist:
                result_serializer = ResultSerializer(data=result_data)
                if not result_serializer.is_valid():
                    raise Exception(result_serializer.errors)
                result_serializer.validated_data['status'] = result_data['status']
                result = result_serializer.save()
            validated_data['result'] = result

        abstracttest_ulid = validated_data.pop('abstracttest')
        try:
            abstracttest = AbstractTest.objects.get(ulid=abstracttest_ulid)
        except AbstractTest.DoesNotExist:
            raise Exception('AbstractTest not found')
        validated_data['abstracttest'] = abstracttest

        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        test_event = TestEvent.objects.create(**validated_data)
        return test_event


class ErrorEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = ErrorEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'error_name',
            'error_msg',
        ]

    def create(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        error_event = ErrorEvent.objects.create(**validated_data)
        return error_event


class GuiFindEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = GuiFindEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'text',
            'objective',
            'success',
            'positions',
        ]

    def create(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        gui_find_event = GuiFindEvent.objects.create(**validated_data)
        return gui_find_event


class GuiClickEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = GuiClickEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'clicktype',
            'modifiers',
            'target'
        ]

    def create(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        gui_click_event = GuiClickEvent.objects.create(**validated_data)
        return gui_click_event


class GuiKeypressEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = GuiKeypressEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'keys',
        ]

    def create(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        gui_keypress_event = GuiKeypressEvent.objects.create(**validated_data)
        return gui_keypress_event


class GuiIdleEventSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = GuiIdleEvent
        fields = [
            'status',
            'ulid',
            'category',
            'error',
            'group_id',
            'timestamp',
            # event specific fields
            'seconds',
        ]

    def create(self, validated_data):
        run_ulid = validated_data.pop('run')
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
        except ExperimentRun.DoesNotExist:
            raise Exception('Run not found')
        validated_data['run'] = run

        status_id = validated_data.pop('status')
        try:
            status = Status.objects.get(id=status_id)
        except Status.DoesNotExist:
            raise Exception('Status not found')
        validated_data['status'] = status

        gui_idle_event = GuiIdleEvent.objects.create(**validated_data)
        return gui_idle_event

def get_event_serializer(event):
    if isinstance(event, CommandEvent):
        return CommandEventSerializer
    elif isinstance(event, TestEvent):
        return TestEventSerializer
    elif isinstance(event, ErrorEvent):
        return ErrorEventSerializer
    elif isinstance(event, GuiFindEvent):
        return GuiFindEventSerializer
    elif isinstance(event, GuiClickEvent):
        return GuiClickEventSerializer
    elif isinstance(event, GuiKeypressEvent):
        return GuiKeypressEventSerializer
    elif isinstance(event, GuiIdleEvent):
        return GuiIdleEventSerializer
    else:
        raise ValueError(f'Unknown event model: {type(event).__name__}')

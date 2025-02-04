from rest_framework import serializers

from experiments.models import *
from django.contrib.auth.models import User
from users.serializers import GiteaUserSerializer
from helperfunctions.gitea import convert_gitea_internal_api_url_to_viewable_url, convert_gitea_internal_api_url_to_external


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'name',
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
    tags = serializers.SerializerMethodField('get_tags', read_only=True)
    post_setup_installations = PostSetupInstallationSerializer(many=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)

    def get_tags(self, obj):
        tag_list = []
        for tag in obj.tags.all():
            tag_list.append(tag.name)
        return tag_list

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


# class TestSerializer(serializers.ModelSerializer):
#     result = ResultSerializer()
#     abstracttest_ulid = serializers.CharField(source='abstracttest.ulid')
#
#     class Meta:
#         model = Test
#         fields = [
#             'ulid',
#             'abstracttest_ulid',
#             'result',
#         ]
#
#     def create(self, validated_data):
#         testfunction_data = validated_data.pop('testfunction')
#         parameters_data = validated_data.pop('parameters')
#
#         if 'tool' in validated_data.keys():
#             tool_data = validated_data.pop('tool')
#             if tool_data:
#                 try:
#                     tool = Tool.objects.get(name=tool_data['name'], command=tool_data['command'])
#                 except Tool.DoesNotExist:
#                     tool_serializer = ToolSerializer(data=tool_data)
#                     tool_serializer.is_valid()
#                     tool = tool_serializer.save()
#                 validated_data['tool'] = tool
#
#         test_parameter_entrys = []
#         for parameter_entry in parameters_data:
#             try:
#                 test_parameter_entry = TestParameterEntry.objects.get(
#                     parameter__name=parameter_entry['parameter']['name'], value=parameter_entry['value'])
#             except TestParameterEntry.DoesNotExist:
#                 test_parameter_entry_serializer = TestParameterEntrySerializer(data=parameter_entry)
#                 test_parameter_entry_serializer.is_valid()
#                 test_parameter_entry = test_parameter_entry_serializer.save()
#             test_parameter_entrys.append(test_parameter_entry)
#
#         try:
#             testfunction = TestFunction.objects.get(name=testfunction_data['name'])
#         except TestFunction.DoesNotExist:
#             testfunction_serializer = TestFunctionSerializer(data=testfunction_data)
#             testfunction_serializer.is_valid()
#             testfunction = testfunction_serializer.save()
#         validated_data['testfunction'] = testfunction
#
#         abstract_test = AbstractTest.objects.create(**validated_data)
#         abstract_test.parameters.set(test_parameter_entrys)
#         return abstract_test


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
    tags = serializers.SerializerMethodField('get_tags', read_only=True)
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

    def get_tags(self, obj):
        tag_list = []
        for tag in obj.tags.all():
            tag_list.append(tag.name)
        return tag_list

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
        status = Status.objects.get(name='success')
        num_successful = ExperimentRun.objects.filter(experiment=obj, result_status=status).count()
        status = Status.objects.get(name='failed')
        num_failed = ExperimentRun.objects.filter(experiment=obj, result_status=status).count()
        return {
            'successful': num_successful,
            'failed': num_failed,
        }


class ExperimentViewableFilesSerializer(ExperimentSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['action_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.action_file)
        ret['testset_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.testset_file)
        ret['metadata_file'] = convert_gitea_internal_api_url_to_viewable_url(instance.metadata_file)
        return ret



class ExperimentRunSerializer(serializers.ModelSerializer):
    # tests = TestSerializer(read_only=True, many=True)
    status = StatusSerializer(read_only=True)
    result_status = StatusSerializer(read_only=True)
    published_by = serializers.CharField(source='published_by.username', read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    experiment = serializers.CharField(source='experiment.name', read_only=True)
    environment = serializers.CharField(source='environment.name', read_only=True)
    events = serializers.SerializerMethodField('get_events', read_only=True)
    duration = serializers.SerializerMethodField('get_duration', read_only=True)

    def get_events(self, obj):
        event_deserialized = []
        for event in sorted(obj.events, key=lambda e: e.timestamp):
            event_serializer = get_event_serializer(event.category)
            # use the serializer to deserialize the event
            event_serializer = event_serializer(event)
            event_deserialized.append(event_serializer.data)

        # filter out all events which status name running if corresponding event with status name finished exists (with same group_id)
        filtered_events = []
        for event in event_deserialized:
            if event['status']['name'] == 'running':
                for other_event in event_deserialized:
                    if other_event['status']['name'] == 'finished' and event['group_id'] == other_event['group_id']:
                        break
                else:
                    filtered_events.append(event)
            else:
                filtered_events.append(event)

        return filtered_events

    def get_duration(self, obj):
        if obj.timestamp_start and obj.timestamp_end:
            return obj.timestamp_end - obj.timestamp_start
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



# class ScenarioSerializer(serializers.ModelSerializer):
#     published_by = GiteaUserSerializer(read_only=True)
#     accepted_by = GiteaUserSerializer(read_only=True)
#     published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     tags = serializers.SerializerMethodField('get_tags', read_only=True)
#
#     class Meta:
#         model = Scenario
#         fields = [
#             'ulid',
#             'name',
#             'experiments',
#             'description',
#             'tags',
#
#             'published_by',
#             'accepted_by',
#             'published_at',
#             'published',
#         ]
#
#     def get_tags(self, obj):
#         tag_list = []
#         for tag in obj.tags.all():
#             tag_list.append(tag.name)
#         return tag_list


class GenericRequestObjectSerializer(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, Experiment):
            return ExperimentSerializer(value).data
        # elif isinstance(value, Scenario):
        #     return ScenarioSerializer(value).data
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

    labels = serializers.SerializerMethodField('get_labels', read_only=True)

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

    def get_labels(self, obj):
        label_list = []
        for label in obj.labels.all():
            label_list.append(label.name)
        return label_list


class ExperimentRunCreateSerializer(serializers.ModelSerializer):
    # tests = TestSerializer(read_only=True, many=True)

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
            'success'
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

def get_event_serializer(event_type: str):
    if event_type == 'command':
        return CommandEventSerializer
    elif event_type == 'test':
        return TestEventSerializer
    elif event_type == 'error':
        return ErrorEventSerializer
    elif event_type == 'gui:find':
        return GuiFindEventSerializer
    elif event_type == 'gui:click':
        return GuiClickEventSerializer
    elif event_type == 'gui:keypress':
        return GuiKeypressEventSerializer
    elif event_type == 'gui:idle':
        return GuiIdleEventSerializer
    else:
        raise Exception(f'Unexpected event type {event_type}')

from rest_framework import serializers

from experiments.models import *


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            'name',
        ]
        extra_kwargs = {
            'name': {
                'validators': [],
            },
        }


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = [
            'name',
        ]


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = [
            'name',
        ]
        extra_kwargs = {
            'name': {
                'validators': [],
            },
        }


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


class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = [
            'name',
            'command',
        ]


class ResultSerializer(serializers.ModelSerializer):
    status = StatusSerializer()

    class Meta:
        model = Result
        fields = [
            'details',
            'status'
        ]

    def create(self, validated_data):
        status_data = validated_data.pop('status')
        try:
            status = Status.objects.get(name=status_data['name'])
        except Status.DoesNotExist:
            status_serializer = StatusSerializer(data=status_data)
            status_serializer.is_valid()
            status = status_serializer.save()
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


class TestParameterEntriesSerializer(serializers.ModelSerializer):
    parameter = TestParameterSerializer()

    class Meta:
        model = TestParameterEntries
        fields = [
            'parameter',
            'value',
        ]

    def create(self, validated_data):
        parameter_data = validated_data.pop('parameter')
        try:
            parameter = TestParameter.objects.get(name=parameter_data['name'], dtype=parameter_data['dtype'])
        except TestParameter.DoesNotExist:
            parameter_serializer = TestParameterSerializer(data=parameter_data)
            parameter_serializer.is_valid()
            parameter = parameter_serializer.save()
        validated_data['parameter'] = parameter

        parameter_entry = TestParameterEntries.objects.create(**validated_data)
        return parameter_entry


class TestFunctionSerializer(serializers.ModelSerializer):
    possible_parameters = TestParameterSerializer(many=True)

    class Meta:
        model = TestFunction
        fields = [
            'name',
            'description',
            'possible_parameters',
        ]
        extra_kwargs = {
            'description': {'required': False},
            'name': {
                'validators': [],
            },
        }

    def create(self, validated_data):
        possible_parameters_data = validated_data.pop('possible_parameters')
        possible_parameters = []
        for parameter_data in possible_parameters_data:
            try:
                parameter = TestParameter.objects.get(name=parameter_data['name'], dtype=parameter_data['dtype'])
            except TestParameter.DoesNotExist:
                parameter = TestParameterSerializer(data=parameter_data)
                parameter.is_valid()
                parameter = parameter.save()
            possible_parameters.append(parameter)

        test_function = TestFunction.objects.create(**validated_data)
        test_function.possible_parameters.set(possible_parameters)
        return test_function


class AbstractTestSerializer(serializers.ModelSerializer):
    testfunction = TestFunctionSerializer()
    parameters = TestParameterEntriesSerializer(many=True)
    tool = ToolSerializer(required=False)

    class Meta:
        model = AbstractTest
        fields = [
            'uuid',
            'name',
            'description',
            'testfunction',
            'parameters',
            'tool',
        ]

    def create(self, validated_data):
        testfunction_data = validated_data.pop('testfunction')
        parameters_data = validated_data.pop('parameters')

        if 'tool' in validated_data.keys():
            tool_data = validated_data.pop('tool')
            try:
                tool = Tool.objects.get(name=tool_data['name'], command=tool_data['command'])
            except Tool.DoesNotExist:
                tool_serializer = ToolSerializer(data=tool_data)
                tool_serializer.is_valid()
                tool = tool_serializer.save()
            validated_data['tool'] = tool

        test_parameter_entrys = []
        for parameter_entry in parameters_data:
            try:
                test_parameter_entry = TestParameterEntries.objects.get(
                    parameter__name=parameter_entry['parameter']['name'], value=parameter_entry['value'])
            except TestParameterEntries.DoesNotExist:
                test_parameter_entry_serializer = TestParameterEntriesSerializer(data=parameter_entry)
                test_parameter_entry_serializer.is_valid()
                test_parameter_entry = test_parameter_entry_serializer.save()
            test_parameter_entrys.append(test_parameter_entry)

        try:
            testfunction = TestFunction.objects.get(name=testfunction_data['name'])
        except TestFunction.DoesNotExist:
            testfunction_serializer = TestFunctionSerializer(data=testfunction_data)
            testfunction_serializer.is_valid()
            testfunction = testfunction_serializer.save()
        validated_data['testfunction'] = testfunction

        abstract_test = AbstractTest.objects.create(**validated_data)
        abstract_test.parameters.set(test_parameter_entrys)
        return abstract_test


class TestSerializer(serializers.ModelSerializer):
    result = ResultSerializer()
    abstracttest_uuid = serializers.CharField(source='abstracttest.uuid')

    class Meta:
        model = Test
        fields = [
            'uuid',
            'abstracttest_uuid',
            'result',
        ]

    def create(self, validated_data):
        abstracttest_data = validated_data.pop('abstracttest')
        result_data = validated_data.pop('result')
        abstracttest = AbstractTest.objects.get(uuid=abstracttest_data['uuid'])

        validated_data['abstracttest'] = abstracttest

        try:
            result = Result.objects.get(status__name=result_data['status']['name'], details=result_data['details'])
        except Result.DoesNotExist:
            result_serializer = ResultSerializer(data=result_data)
            result_serializer.is_valid()
            result = result_serializer.save()
        validated_data['result'] = result

        test = Test.objects.create(**validated_data)
        return test


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class ExperimentSerializer(serializers.ModelSerializer):
    run_counts = serializers.SerializerMethodField('get_run_counts', read_only=True)
    abstract_tests = AbstractTestSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField('get_tags', read_only=True)
    publisher_name = serializers.SerializerMethodField('get_publisher_name', read_only=True)
    publish_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    os_info = OsInfoSerializer(read_only=True)
    action_file = serializers.SerializerMethodField('get_action_file', read_only=True)
    testset_file = serializers.SerializerMethodField('get_testset_file', read_only=True)
    # experiment_runs = serializers.SerializerMethodField('get_experiment_runs', read_only=True)

    def get_action_file(self, obj):
        return f'api/file/actionfile/{obj.uuid}/'

    def get_testset_file(self, obj):
        return f'api/file/testsetfile/{obj.uuid}/'

    class Meta:
        model = Experiment
        fields = [
            'uuid',
            'name',
            'description',
            'publisher_name',
            'publish_date',
            'tags',
            'abstract_tests',
            'run_counts',
            'os_info',
            'action_file',
            'testset_file',
            # 'experiment_runs',
        ]
        extra_kwargs = {
            'tags': {'read_only': True},
            'abstract_tests': {'read_only': True},
        }

    def get_experiment_runs(self, obj):
        experiment_runs = ExperimentRun.objects.filter(experiment=obj)
        serializer = ExperimentRunSerializer(experiment_runs, many=True)
        return serializer.data

    def get_tags(self, obj):
        tag_list = []
        for tag in obj.tags.all():
            tag_list.append(tag.name)
        return tag_list

    def get_publisher_name(self, obj):
        if obj.publisher is not None:
            return obj.publisher.username
        return None

    def get_run_counts(self, obj):
        status = Status.objects.get(name='success')
        num_successful = ExperimentRun.objects.filter(experiment=obj, status=status).count()
        status = Status.objects.get(name='failed')
        num_failed = ExperimentRun.objects.filter(experiment=obj, status=status).count()
        return {
            'successful': num_successful,
            'failed': num_failed,
        }


class ExperimentRunSerializer(serializers.ModelSerializer):
    tests = TestSerializer(read_only=True, many=True)
    status = StatusSerializer(read_only=True)
    publisher_name = serializers.SerializerMethodField('get_publisher_name', read_only=True)
    experiment = serializers.CharField(source='experiment.name', read_only=True)
    logfile = serializers.SerializerMethodField('get_logfile', read_only=True)

    def get_logfile(self, obj):
        if obj.logfile:
            return f'api/file/logfile/{obj.uuid}/'
        return None

    class Meta:
        model = ExperimentRun
        fields = [
            'uuid',
            'publisher_name',
            'publish_date',
            'timestamp_start',
            'timestamp_end',
            'tests',
            'status',
            'experiment',
            'logfile',
        ]

    def get_publisher_name(self, obj):
        if obj.publisher is not None:
            return obj.publisher.username
        return None


class ScenarioSerializer(serializers.ModelSerializer):
    publisher_name = serializers.SerializerMethodField('get_publisher_name', read_only=True)
    publish_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    # publisher_icon = serializers.SerializerMethodField('get_publisher_icon', read_only=True)
    tags = serializers.SerializerMethodField('get_tags', read_only=True)

    class Meta:
        model = Scenario
        fields = [
            'uuid',
            'name',
            'description',
            'publish_date',
            'publisher_name',
            'tags',
            'experiments',
        ]

    def get_tags(self, obj):
        tag_list = []
        for tag in obj.tags.all():
            tag_list.append(tag.name)
        return tag_list

    def get_publisher_name(self, obj):
        return obj.publisher.username


class RequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestStatus
        fields = [
            'name',
        ]


class RequestListSerializer(serializers.ModelSerializer):
    requestor = serializers.SerializerMethodField('get_requestor', read_only=True)
    supervisor = serializers.SerializerMethodField('get_supervisor', read_only=True)
    supervisor_assigned_by = serializers.SerializerMethodField('get_supervisor_assigned_by', read_only=True)
    status = RequestStatusSerializer(read_only=True)
    labels = LabelSerializer(read_only=True, many=True)

    def get_requestor(self, obj):
        if obj.requestor is None:
            return None
        return obj.requestor.username

    def get_supervisor(self, obj):
        if obj.supervisor is None:
            return None
        return obj.supervisor.username

    def get_supervisor_assigned_by(self, obj):
        if obj.supervisor_assigned_by is None:
            return None
        return obj.supervisor_assigned_by.username

    class Meta:
        model = Request
        fields = [
            'title',
            'uuid',
            'description',
            'last_changed',
            'category_type',
            'requestor',
            'request_creation_date',
            'supervisor',
            'supervisor_assigned_by',
            'status',
            'labels',
        ]


class RequestSerializer(RequestListSerializer):
    category = serializers.SerializerMethodField('get_category', read_only=True)

    def get_category(self, obj):
        if obj.category_type == 'scenario':
            return {
                'type': obj.category_type,
                'category': ScenarioSerializer(obj.scenario).data,
            }
        elif obj.category_type == 'experiment':
            return {
                'type': obj.category_type,
                'category': ExperimentSerializer(obj.experiment).data,
            }
        else:
            return {
                'type': 'not supported',
                'category': None,
            }

    class Meta:
        model = Request
        fields = [
            'title',
            'uuid',
            'description',
            'category',
            'category_type',
            'last_changed',
            'category_type',
            'requestor',
            'request_creation_date',
            'supervisor',
            'supervisor_assigned_by',
            'status',
            'labels',
        ]


# serializers specialized for creating objects
class ExperimentCreateSerializer(serializers.ModelSerializer):
    action_file = serializers.FileField(write_only=True)
    testset_file = serializers.FileField(write_only=True)

    class Meta:
        model = Experiment
        fields = [
            'uuid',
            'name',
            'description',
            'action_file',
            'testset_file',
            'publisher',
            'publish_date',
            'published',
            'os_info',
        ]


class ExperimentRunCreateSerializer(serializers.ModelSerializer):
    tests = TestSerializer(read_only=True, many=True)

    class Meta:
        model = ExperimentRun
        fields = [
            'uuid',
            'publisher',
            'publish_date',
            'timestamp_start',
            'timestamp_end',
            'experiment',
            'tests',
            'status',
            'experiment',
            'logfile',
        ]
        extra_kwargs = {
            'experiment': {'validators': []},
        }


class ScenarioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = [
            'uuid',
            'name',
            'description',
            'publish_date',
            'publisher',
            'published',
            'tags',
            'experiments',
        ]


class RequestCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = [
            'title',
            'uuid',
            'description',
            'category_type',
            'last_changed',
            'scenario',
            'experiment',
            'requestor',
            'request_creation_date',
            'supervisor',
            'supervisor_assigned_by',
            'status',
        ]
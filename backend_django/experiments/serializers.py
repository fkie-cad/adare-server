from rest_framework import serializers

from experiments.models import *
from django.contrib.auth.models import User
from users.serializers import GiteaUserSerializer


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


class EnvironmentSerializer(serializers.ModelSerializer):
    os_info = OsInfoSerializer()

    class Meta:
        model = Environment
        fields = [
            'name',
            'vagrantbox',
            'description',
            'os_info',
        ]


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


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = [
            'package',
            'version',
            'relation',
        ]


class TestFunctionSetSerializer(serializers.ModelSerializer):
    requirements = RequirementSerializer(many=True)
    published_by = GiteaUserSerializer()
    accepted_by = GiteaUserSerializer()

    class Meta:
        model = TestfunctionSet
        fields = [
            'name',
            'description',
            'requirements',
            'sha256hash',
            'sha256testfunctionset',
            'sha256requirements',
            'published_by',
            'accepted_by',
            'published_at',
            'published',
        ]



class AbstractTestSerializer(serializers.ModelSerializer):
    testfunction = TestFunctionSerializer()
    parameters = TestParameterEntrySerializer(many=True)
    tool = ToolSerializer(required=False, allow_null=True)

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
        testfunction_data = validated_data.pop('testfunction')
        parameters_data = validated_data.pop('parameters')

        if 'tool' in validated_data.keys():
            tool_data = validated_data.pop('tool')
            if tool_data:
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
                test_parameter_entry = TestParameterEntry.objects.get(
                    parameter__name=parameter_entry['parameter']['name'], value=parameter_entry['value'])
            except TestParameterEntry.DoesNotExist:
                test_parameter_entry_serializer = TestParameterEntrySerializer(data=parameter_entry)
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


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class ExperimentSerializer(serializers.ModelSerializer):
    run_counts = serializers.SerializerMethodField('get_run_counts', read_only=True)
    abstract_tests = AbstractTestSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField('get_tags', read_only=True)
    environments = EnvironmentSerializer(read_only=True, many=True)
    published_by = GiteaUserSerializer(read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    accepted_by = GiteaUserSerializer(read_only=True)

    class Meta:
        model = Experiment
        fields = [
            'uuid',
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
            'accepted_by',
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
    published_by = GiteaUserSerializer(read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
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
            'published_by',
            'published_at',
            'timestamp_start',
            'timestamp_end',
            'tests',
            'status',
            'experiment',
            'logfile',
        ]


class ScenarioSerializer(serializers.ModelSerializer):
    published_by = GiteaUserSerializer(read_only=True)
    accepted_by = GiteaUserSerializer(read_only=True)
    published_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    tags = serializers.SerializerMethodField('get_tags', read_only=True)

    class Meta:
        model = Scenario
        fields = [
            'uuid',
            'name',
            'experiments',
            'description',
            'tags',

            'published_by',
            'accepted_by',
            'published_at',
            'published',
        ]

    def get_tags(self, obj):
        tag_list = []
        for tag in obj.tags.all():
            tag_list.append(tag.name)
        return tag_list


class GenericRequestObjectSerializer(serializers.Field):
    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, Experiment):
            return ExperimentSerializer(value).data
        elif isinstance(value, Scenario):
            return ScenarioSerializer(value).data
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
            'uuid',
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
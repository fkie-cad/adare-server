from django.contrib.auth import authenticate
from django.contrib.auth.models import User
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
            'test_name',
            'test_description',
            'possible_parameters',
        ]
        extra_kwargs = {
            'test_description': {'required': False},
            'test_name': {
                'validators': [],
            },
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
                test_parameter_entry = TestParameterEntries.objects.get(parameter__name=parameter_entry['parameter']['name'], value=parameter_entry['value'])
            except TestParameterEntries.DoesNotExist:
                test_parameter_entry_serializer = TestParameterEntriesSerializer(data=parameter_entry)
                test_parameter_entry_serializer.is_valid()
                test_parameter_entry = test_parameter_entry_serializer.save()
            test_parameter_entrys.append(test_parameter_entry)

        try:
            testfunction = TestFunction.objects.get(name=testfunction_data['name'], test_name=testfunction_data['test_name'])
        except TestFunction.DoesNotExist:
            testfunction_serializer = TestFunctionSerializer(data=testfunction_data)
            testfunction_serializer.is_valid()
            testfunction = testfunction_serializer.save()
        validated_data['testfunction'] = testfunction

        abstract_test = AbstractTest.objects.create(**validated_data)
        abstract_test.parameters.set(test_parameter_entrys)
        return abstract_test


class TestSerializer(serializers.ModelSerializer):
    abstracttest = AbstractTestSerializer(read_only=True)
    result = ResultSerializer(read_only=True)

    class Meta:
        model = Test
        fields = '__all__'


class CurrentUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username',)


class ExperimentSerializer(serializers.ModelSerializer):
    run_counts = serializers.SerializerMethodField('get_run_counts', read_only=True)
    abstract_tests = AbstractTestSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField('get_tags', read_only=True)
    publisher_name = serializers.SerializerMethodField('get_publisher_name', read_only=True)

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
    experiment = ExperimentSerializer(read_only=True)
    tests = TestSerializer(read_only=True, many=True)
    os_info = OsInfoSerializer(read_only=True)
    status = StatusSerializer(read_only=True)

    class Meta:
        model = ExperimentRun
        fields = '__all__'


class ScenarioSerializer(serializers.ModelSerializer):
    publisher_name = serializers.SerializerMethodField('get_publisher_name', read_only=True)
    # publisher_icon = serializers.SerializerMethodField('get_publisher_icon', read_only=True)

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

    def get_publisher_name(self, obj):
        return obj.publisher.username

    # def get_publisher_icon(self, obj):
    #     if obj.publisher.profile.avatar:
    #         return obj.publisher.profile.avatar.url
    #     else:
    #         return None


class RequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = '__all__'


class RequestSerializer(serializers.ModelSerializer):
    status = RequestStatusSerializer(read_only=True)
    user = CurrentUserSerializer(read_only=True)

    class Meta:
        model = Request
        fields = '__all__'

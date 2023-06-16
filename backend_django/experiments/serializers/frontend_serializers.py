from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from experiments.models import *


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'


class OsInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OsInfo
        fields = '__all__'


class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):
    status = StatusSerializer(read_only=True)

    class Meta:
        model = Result
        fields = '__all__'


class TestParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestParameter
        fields = '__all__'


class TestParameterEntriesSerializer(serializers.ModelSerializer):
    parameter = TestParameterSerializer()

    class Meta:
        model = TestParameterEntries
        fields = '__all__'


class TestFunctionSerializer(serializers.ModelSerializer):
    possible_parameters = TestParameterSerializer(many=True, read_only=True)

    class Meta:
        model = TestFunction
        fields = '__all__'


class AbstractTestSerializer(serializers.ModelSerializer):
    testfunction = TestFunctionSerializer(read_only=True)
    parameters = TestParameterEntriesSerializer(many=True, read_only=True)
    tool = ToolSerializer(read_only=True)

    class Meta:
        model = AbstractTest
        fields = '__all__'


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
    number_successful_experiments = serializers.SerializerMethodField('count_successful_experiments')
    number_failed_experiments = serializers.SerializerMethodField('count_failed_experiments')
    publisher = CurrentUserSerializer(read_only=True)
    tests = AbstractTestSerializer(read_only=True, many=True)

    class Meta:
        model = Scenario
        fields = '__all__'

    def count_successful_experiments(self, obj):
        scenario = Scenario.objects.get(uuid=obj.uuid)
        status = Status.objects.get(name='success')
        return ExperimentRun.objects.filter(scenario=scenario, status=status).count()

    def count_failed_experiments(self, obj):
        scenario = Scenario.objects.get(uuid=obj.uuid)
        status = Status.objects.get(name='failed')
        return ExperimentRun.objects.filter(scenario=scenario, status=status).count()


class ExperimentRunSerializer(serializers.ModelSerializer):
    experiment = ExperimentSerializer(read_only=True)
    tests = TestSerializer(read_only=True, many=True)
    os_info = OsInfoSerializer(read_only=True)
    status = StatusSerializer(read_only=True)

    class Meta:
        model = ExperimentRun
        fields = '__all__'


class ScenarioSerializer(serializers.ModelSerializer):
    experiment = ExperimentSerializer(read_only=True)
    experiment_run = ExperimentRunSerializer(read_only=True)

    class Meta:
        model = Experiment
        fields = '__all__'


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

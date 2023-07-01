from rest_framework import views
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import rest_framework.generics as generics
import rest_framework.status as http_status_codes
import django_filters.rest_framework
from django.utils.timezone import make_aware

from datetime import datetime

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from permissions import HasGroupPermission

from experiments.models import Experiment, ExperimentRun, Scenario, Tag, AbstractTest
from experiments.filters import ScenarioFilter, ExperimentFilter
from experiments.serializers import ExperimentRunSerializer, ScenarioSerializer, ExperimentSerializer, TagSerializer, AbstractTestSerializer


class ExperimentRunListView(generics.ListAPIView, generics.RetrieveAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'uuid'


class ExperimentListView(generics.ListAPIView, generics.RetrieveAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ExperimentFilter
    # only for retrieve
    lookup_field = 'uuid'


class ExperimentByScenarioListView(generics.ListAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ExperimentFilter
    # only for retrieve
    lookup_field = 'uuid'

    def get_queryset(self):
        scenario_uuid = self.kwargs['uuid']
        return Scenario.objects.get(uuid=scenario_uuid).experiments.all()


class ExperimentRunCreateView(generics.CreateAPIView):
    serializer_class = ExperimentRun
    queryset = ExperimentRun.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }
    # only for retrieve
    lookup_field = 'uuid'


class ScenarioListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ScenarioSerializer
    queryset = Scenario.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ScenarioFilter


class ScenarioCreateView(generics.CreateAPIView):
    serializer_class = ScenarioSerializer
    queryset = Scenario.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }

    def create(self, request, *args, **kwargs):
        data = request.data
        experiment_uuids = data.pop('experiments_uuids')

        data['publisher'] = request.user.id
        data['publish_date'] = make_aware(datetime.now())
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        scenario = serializer.save()
        experiments = Experiment.objects.filter(uuid__in=experiment_uuids)
        scenario.experiments.add(*experiments)
        scenario.save()
        return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)


class ExperimentCreateView(generics.CreateAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }

    def create(self, request, *args, **kwargs):
        data = request.data
        abstract_tests = data.pop('abstract_tests')
        tags = data.pop('tags')

        data['publisher'] = request.user.id
        data['publish_date'] = make_aware(datetime.now())
        data['published'] = True
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        experiment = serializer.save()

        # create or get AbstractTests
        t_ser = AbstractTestSerializer(data=abstract_tests, many=True)
        t_ser.is_valid(raise_exception=True)
        abstract_tests_objects = t_ser.save()
        experiment.abstract_tests.add(*abstract_tests_objects)

        # create or get Tags
        tags_objects = []
        non_existing_tags = []
        for tag in tags:
            try:
                tag_object = Tag.objects.get(name=tag['name'])
                tags_objects.append(tag_object)
            except Tag.DoesNotExist:
                non_existing_tags.append(tag)
        tag_serializer = TagSerializer(data=non_existing_tags, many=True)
        tag_serializer.is_valid(raise_exception=False)
        tags_objects += tag_serializer.save()
        experiment.tags.add(*tags_objects)

        # save added tags and abstract_tests
        experiment.save()
        return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)

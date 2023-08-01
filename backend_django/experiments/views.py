import rest_framework.parsers
from rest_framework import views
from rest_framework.decorators import permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
import rest_framework.generics as generics
import rest_framework.status as http_status_codes
import django_filters.rest_framework
from django.utils.timezone import make_aware
from experiments.parsers import MultiPartJSONParser

from datetime import datetime

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from permissions import HasGroupPermission

from experiments.models import *
from experiments.filters import ScenarioFilter, ExperimentFilter, RequestFilter
from experiments.serializers import *


def create_scenario(data, publisher_id, published=False):
    experiment_uuids = data.pop('experiments_uuids')
    tags = data.pop('tags')
    tag_objects = []
    for tag in tags:
        try:
            tag_object = Tag.objects.get(**tag)
        except Tag.DoesNotExist:
            tag_serializer = TagSerializer(data=tag)
            tag_serializer.is_valid(raise_exception=True)
            tag_object = tag_serializer.save()
        tag_objects.append(tag_object)

    data['publisher'] = publisher_id
    data['publish_date'] = make_aware(datetime.now())
    data['published'] = published
    serializer = ScenarioCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    scenario = serializer.save()
    experiments = Experiment.objects.filter(uuid__in=experiment_uuids)
    scenario.experiments.set(experiments)
    scenario.tags.set(tag_objects)
    scenario.save()
    return scenario


def create_experiment(data, publisher_id, action_file, testset_file, published=False):
    data['action_file'] = action_file
    data['testset_file'] = testset_file

    abstract_tests = data.pop('abstract_tests')
    tags = data.pop('tags')
    os_info = data.pop('os_info')

    scenario = None
    if 'scenario_uuid' in data.keys():
        scenario_uuid = data.pop('scenario_uuid')
        scenario = Scenario.objects.get(uuid=scenario_uuid)

    # create or get OSInfo
    try:
        osinfo_object = OsInfo.objects.get(**os_info)
    except OsInfo.DoesNotExist:
        os_info_serializer = OsInfoSerializer(data=os_info)
        os_info_serializer.is_valid(raise_exception=True)
        osinfo_object = os_info_serializer.save()

    data['publisher'] = publisher_id
    data['publish_date'] = make_aware(datetime.now())
    data['published'] = published
    data['os_info'] = osinfo_object.id
    serializer = ExperimentCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    experiment = serializer.save()

    # create or get AbstractTests
    abstract_tests_objects = []
    for abstract_test in abstract_tests:
        try:
            abstract_test_object = AbstractTest.objects.get(uuid=abstract_test['uuid'])
        except AbstractTest.DoesNotExist:
            abstract_test_serializer = AbstractTestSerializer(data=abstract_test)
            abstract_test_serializer.is_valid(raise_exception=True)
            abstract_test_object = abstract_test_serializer.save()
        abstract_tests_objects.append(abstract_test_object)

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

    experiment.save()

    if scenario:
        scenario.experiments.add(experiment)

    return experiment


class ExperimentRunListView(generics.ListAPIView, generics.RetrieveAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'uuid'


class ExperimentListView(generics.ListAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.filter(published=True).all()
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExperimentFilter
    search_fields = ['name', 'uuid', 'tags__name', 'description', 'publisher__username', 'publish_date']
    pagination_class = LimitOffsetPagination


class ExperimentRetrieveView(generics.RetrieveAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'uuid'


class ExperimentByScenarioListView(generics.ListAPIView):
    serializer_class = ExperimentSerializer
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ExperimentFilter
    # only for retrieve
    lookup_field = 'uuid'

    def get_queryset(self):
        scenario_uuid = self.kwargs['uuid']
        return Scenario.objects.get(uuid=scenario_uuid).experiments.filter(published=True).all()


class ScenarioListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ScenarioSerializer
    queryset = Scenario.objects.filter(published=True).all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ScenarioFilter
    search_fields = ['name', 'uuid', 'tags__name', 'description', 'publisher__username', 'publish_date', 'experiments__name']
    pagination_class = LimitOffsetPagination


class ScenarioFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Scenario.objects.filter(published=True).all()

    def get(self, request, *args, **kwargs):
        field = kwargs['field']
        if field == 'tags':
            tags = Tag.objects.all()
            return Response([tag.name for tag in tags])
        elif field == 'publisher':
            publishers = User.objects.all()
            return Response([publisher.username for publisher in publishers])
        elif field == 'experiments':
            experiments = Experiment.objects.filter(published=True).all()
            return Response([experiment.name for experiment in experiments])
        else:
            return Response('Field not found', status=http_status_codes.HTTP_404_NOT_FOUND)


class ExperimentFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Experiment.objects.filter(published=True).all()

    def get(self, request, *args, **kwargs):
        field = kwargs['field']
        if field == 'tags':
            tags = Tag.objects.all()
            return Response([tag.name for tag in tags])
        else:
            return Response('Field not found', status=http_status_codes.HTTP_404_NOT_FOUND)


class RequestFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Request.objects.all()

    def get(self, request, *args, **kwargs):
        field = kwargs['field']
        if field == 'status':
            status = RequestStatus.objects.all()
            return Response([status.name for status in status])
        elif field == 'category':
            return Response(['experiment', 'scenario'])
        else:
            return Response('Field not found', status=http_status_codes.HTTP_404_NOT_FOUND)


class RequestListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestListSerializer
    queryset = Request.objects.all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RequestFilter
    pagination_class = LimitOffsetPagination


class RequestRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'uuid'


class RequestAcceptView(generics.UpdateAPIView):
    permission_classes = [HasGroupPermission]
    required_groups = {
        'PUT': ['supervisor'],
    }
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'uuid'

    def update(self, request, *args, **kwargs):
        request = self.get_object()
        if request.experiment:
            request.experiment.published = True
            request.experiment.publish_date = make_aware(datetime.now())
            request.experiment.save()
        status = RequestStatus.objects.get(name='accepted')
        request.status = status
        request.save()
        return Response(f'Request {request.uuid} accepted successfully', status=http_status_codes.HTTP_200_OK)


class RequestRejectView(generics.UpdateAPIView):
    permission_classes = [HasGroupPermission]
    required_groups = {
        'PUT': ['supervisor'],
    }
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'uuid'

    def update(self, request, *args, **kwargs):
        request = self.get_object()
        status = RequestStatus.objects.get(name='rejected')
        request.status = status
        request.save()
        return Response(f'Request {request.uuid} rejected successfully', status=http_status_codes.HTTP_200_OK)


class RequestAssignView(generics.UpdateAPIView):
    permission_classes = [HasGroupPermission]
    required_groups = {
        'PUT': ['supervisor'],
    }
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'uuid'

    def update(self, request, *args, **kwargs):
        request_obj = self.get_object()
        assigned_by = request.user
        supervisor = User.objects.get(username=kwargs['username'])
        if not supervisor.groups.filter(name='supervisor').exists():
            return Response(f'User {supervisor.username} is not a supervisor',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        request_obj.supervisor_assigned_by = assigned_by
        request_obj.supervisor = supervisor
        status = RequestStatus.objects.get(name='assigned')
        request_obj.status = status
        request_obj.save()
        return Response(f'Request {request_obj.uuid} assigned successfully', status=http_status_codes.HTTP_200_OK)


# specialized views for creating objects with nested objects
class ScenarioCreateView(generics.CreateAPIView):
    serializer_class = ScenarioCreateSerializer
    queryset = Scenario.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }

    def create(self, request, *args, **kwargs):
        data = request.data
        scenario = create_scenario(data, request.user.id, published=True)
        return Response(f'Scenario {scenario.uuid} created successfully', status=http_status_codes.HTTP_201_CREATED)


class ExperimentCreateView(generics.CreateAPIView):
    queryset = Experiment.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }
    parser_classes = [MultiPartJSONParser]

    def create(self, request, *args, **kwargs):
        data = request.data

        action_file = request.FILES.get('action_file')
        testset_file = request.FILES.get('testset_file')

        experiment = create_experiment(data, request.user.id, action_file, testset_file, published=True)

        return Response(f'experiment {experiment.uuid} created successfully', status=http_status_codes.HTTP_201_CREATED)


class ExperimentRunCreateView(generics.CreateAPIView):
    serializer_class = ExperimentRunCreateSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }

    def create(self, request, *args, **kwargs):
        data = request.data
        experimentrun_uuid = data['uuid']
        experiment_uuid = data.pop('experiment_uuid')
        status = data.pop('status')

        # get experiment for experiment run
        try:
            experiment = Experiment.objects.get(uuid=experiment_uuid)
        except Experiment.DoesNotExist:
            return Response(f'Experiment with uuid {experiment_uuid} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['experiment'] = experiment.uuid

        # check if experiment is published
        if not experiment.published:
            return Response(f'Experiment with uuid {experiment_uuid} is not published',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)

        # check if experiment run already exists
        try:
            experiment_run = ExperimentRun.objects.get(uuid=experimentrun_uuid)
            return Response(f'Experiment run for experiment {experiment_uuid} already exists',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        except ExperimentRun.DoesNotExist:
            pass

        # create or get Status
        try:
            status_object = Status.objects.get(name=status['name'])
        except Status.DoesNotExist:
            return Response(f'Status with name {status} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['status'] = status_object.id

        tests = data.pop('tests')
        test_object_list = []
        for test in tests:
            try:
                test_object = Test.objects.get(uuid=test['uuid'])
            except Test.DoesNotExist:
                test_serializer = TestSerializer(data=test)
                test_serializer.is_valid(raise_exception=True)
                test_object = test_serializer.save()
            test_object_list.append(test_object)

        # check if all tests of the experiment are included in the experiment run and vice versa
        uuid_tests = [test.abstracttest.uuid for test in test_object_list]
        uuid_abstract_tests = [abstract_test.uuid for abstract_test in experiment.abstract_tests.all()]
        if not set(uuid_abstract_tests).issubset(set(uuid_tests)):
            return Response(f'Not all tests of experiment {experiment_uuid} are included in the experiment run',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        if not set(uuid_tests).issubset(set(uuid_abstract_tests)):
            return Response(f'Not all tests of experiment run {experimentrun_uuid} are included in the experiment',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)

        data['publisher'] = request.user.id
        data['publish_date'] = make_aware(datetime.now())
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        experiment_run = serializer.save()
        experiment_run.tests.set(test_object_list)
        return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)


class RequestsExperimentCreateView(generics.CreateAPIView):
    serializer_class = RequestCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartJSONParser]

    def create(self, request, *args, **kwargs):
        data = request.data

        action_file = request.FILES.get('action_file')
        testset_file = request.FILES.get('testset_file')

        if 'experiment' in data.keys():
            experiment_data = data.pop('experiment')
        else:
            return Response('Request does not contain an experiment', status=http_status_codes.HTTP_400_BAD_REQUEST)

        experiment = create_experiment(experiment_data, request.user.id, action_file, testset_file)

        # create request
        data['requestor'] = request.user.id
        data['supervisor'] = None
        data['supervisor_assigned_by'] = None
        data['last_changed'] = make_aware(datetime.now())
        data['request_creation_date'] = make_aware(datetime.now())

        status = 'not assigned'
        try:
            status_object = RequestStatus.objects.get(name=status)
        except RequestStatus.DoesNotExist:
            return Response(f'Status with name {status} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['status'] = status_object.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        request_object = serializer.save()

        # add scenario or experiment to request
        request_object.experiment = experiment

        request_object.save()
        return Response(f'request {request_object.uuid} created successfully',
                        status=http_status_codes.HTTP_201_CREATED)


class RequestsScenarioCreateView(generics.CreateAPIView):
    serializer_class = RequestCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartJSONParser]

    def create(self, request, *args, **kwargs):
        data = request.data

        scenario = None
        if 'scenario' in data.keys():
            scenario_data = data.pop('scenario')
        else:
            return Response('Request does not contain an scenario', status=http_status_codes.HTTP_400_BAD_REQUEST)

        scenario = create_scenario(scenario_data, request.user.id)

        # create request
        data['requestor'] = request.user.id
        data['supervisor'] = None
        data['supervisor_assigned_by'] = None
        data['last_changed'] = make_aware(datetime.now())
        data['request_creation_date'] = make_aware(datetime.now())

        status = 'not assigned'
        try:
            status_object = RequestStatus.objects.get(name=status)
        except RequestStatus.DoesNotExist:
            return Response(f'Status with name {status} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['status'] = status_object.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        request_object = serializer.save()

        # add scenario or experiment to request
        request_object.scenario = scenario

        request_object.save()
        return Response(f'request {request_object.uuid} created successfully',
                        status=http_status_codes.HTTP_201_CREATED)


class RequestCancelView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'uuid'

    def delete(self, request, *args, **kwargs):
        request_obj = self.get_object()
        if request_obj.requestor == request.user:
            # get experiment or scenario
            if request_obj.experiment:
                request_obj.experiment.delete()
            if request_obj.scenario:
                request_obj.scenario.delete()
            if request_obj:
                request_obj.delete()
            return Response(f'Request {request_obj.uuid} deleted successfully', status=http_status_codes.HTTP_200_OK)
        return Response(f'You are not allowed to delete request {request_obj.uuid}',
                        status=http_status_codes.HTTP_403_FORBIDDEN)

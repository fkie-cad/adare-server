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
from django.db.models import Count, Max, Q
from experiments.models import Event
from django.contrib.auth.models import User
from helperfunctions.gitea import convert_gitea_internal_api_url_to_viewable_url
import json
from django.db import transaction

from datetime import datetime
from permissions import HasGroupPermission

from experiments.models import *
# from experiments.filters import ScenarioFilter, ExperimentFilter, RequestFilter, ExperimentRunFilter
from experiments.serializers import *


class ExperimentRunListView(generics.ListAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [AllowAny]
    #filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    #filterset_class = ExperimentRunFilter
    search_fields = ['ulid', 'experiment__name', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentRunRetrieveView(generics.RetrieveAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'ulid'


class ExperimentListView(generics.ListAPIView):
    serializer_class = ExperimentViewableFilesSerializer
    queryset = Experiment.objects.filter(published=True).all()
    permission_classes = [IsAuthenticated]
    #filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    #filterset_class = ExperimentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentView(generics.RetrieveAPIView):
    serializer_class = ExperimentViewableFilesSerializer
    queryset = Experiment.objects.filter(published=True).all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'ulid'


class TestFunctionListView(generics.ListAPIView):
    serializer_class = TestFunctionSetSerializer
    queryset = TestfunctionSet.objects.filter(published=True).all()
    permission_classes = [AllowAny]
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentDownloadView(generics.RetrieveAPIView):
    serializer_class = ExperimentSerializer
    permission_classes = [AllowAny]
    queryset = Experiment.objects.filter(published=True).all()
    lookup_field = 'ulid'


class TestfunctionDownloadView(generics.RetrieveAPIView):
    serializer_class = TestFunctionSetSerializer
    permission_classes = [AllowAny]
    queryset = TestfunctionSet.objects.filter(published=True).all()
    lookup_field = 'name'


class EnvironmentDownloadView(generics.RetrieveAPIView):
    serializer_class = EnvironmentSerializer
    permission_classes = [AllowAny]
    queryset = Environment.objects.filter(published=True).all()
    lookup_field = 'name'


class ExperimentHashToMetadataView(generics.RetrieveAPIView):
    serializer_class = ExperimentMetadataSerializer
    permission_classes = [AllowAny]
    queryset = Experiment.objects.all()
    lookup_field = 'sha256hash'


class EnvironmentHashToMetadataView(generics.RetrieveAPIView):
    serializer_class = EnvironmentMetadataSerializer
    permission_classes = [AllowAny]
    queryset = Environment.objects.all()
    lookup_field = 'sha256hash'


class TestfunctionHashToMetadataView(generics.RetrieveAPIView):
    serializer_class = TestFunctionSetMetadataSerializer
    permission_classes = [AllowAny]
    queryset = TestfunctionSet.objects.all()
    lookup_field = 'sha256hash'




# class ExperimentByScenarioListView(generics.ListAPIView):
#     serializer_class = ExperimentSerializer
#     permission_classes = [AllowAny]
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
#     filterset_class = ExperimentFilter
#     # only for retrieve
#     lookup_field = 'ulid'
#
#     def get_queryset(self):
#         scenario_ulid = self.kwargs['ulid']
#         return Scenario.objects.get(ulid=scenario_ulid).experiments.filter(published=True).all()
#
#
# class ScenarioListView(generics.ListAPIView):
#     permission_classes = [AllowAny]
#     serializer_class = ScenarioSerializer
#     queryset = Scenario.objects.filter(published=True).all()
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ScenarioFilter
#     search_fields = ['name', 'ulid', 'tags__name', 'description', 'publisher__username', 'publish_date',
#                      'experiments__name']
#     pagination_class = LimitOffsetPagination


# class ScenarioFilterOptionsView(generics.RetrieveAPIView):
#     permission_classes = [AllowAny]
#     queryset = Scenario.objects.filter(published=True).all()
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ScenarioFilter
#     search_fields = ['name', 'ulid', 'tags__name', 'description', 'publisher__username', 'publish_date',
#                      'experiments__name']
#
#     def get(self, request, *args, **kwargs):
#         # get all tags of all scenarios in queryset
#         tags = self.filter_queryset(self.get_queryset()).values_list('tags__name', flat=True).distinct()
#
#         return Response({
#             'tags': tags,
#         }, status=http_status_codes.HTTP_200_OK)


class ExperimentFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Experiment.objects.filter(published=True).all()
    #filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    #filterset_class = ExperimentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'publisher__username', 'publish_date']

    def get(self, request, *args, **kwargs):
        # get all tags of all experiments in queryset
        tags = self.filter_queryset(self.get_queryset()).values_list('tags__name', flat=True).distinct()
        # check if tags is a list only containing None
        if len(tags) == 1 and tags[0] is None:
            tags = []

        # get max number of successfull experiment runs through all experiments in queryset
        max_success = self.filter_queryset(self.get_queryset()).annotate(
            success_count=Count('experiment_runs', filter=Q(experiment_runs__status__name='success'))
        ).aggregate(Max('success_count'))['success_count__max']

        # get max number of failed experiment runs through all experiments in queryset
        max_failed = self.filter_queryset(self.get_queryset()).annotate(
            failed_count=Count('experiment_runs', filter=Q(experiment_runs__status__name='failed'))
        ).aggregate(Max('failed_count'))['failed_count__max']

        # get total number of experiment runs through all experiments in queryset
        total_count = self.filter_queryset(self.get_queryset()).annotate(
            total_count=Count('experiment_runs')
        ).aggregate(Max('total_count'))['total_count__max']

        return Response({
            'tags': tags,
            'max_success': max_success,
            'max_failed': max_failed,
            'total_count': total_count,
        }, status=http_status_codes.HTTP_200_OK)


class RequestFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = []
    queryset = Request.objects.all()
    #filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    #filterset_class = RequestFilter
    search_fields = ['title', 'ulid', 'description', 'status__name', 'requestor__username', 'supervisor__username',
                     'last_changed', 'labels__name']

    def get(self, request, *args, **kwargs):
        # get all status names of all requests in queryset
        status = self.filter_queryset(self.get_queryset()).values_list('gitea_pr_status', flat=True).distinct()
        # get all object types (objectives) of all requests in queryset
        category_type = self.filter_queryset(self.get_queryset()).values_list('objective__model', flat=True).distinct()
        # get all labels of all requests in queryset
        labels = self.filter_queryset(self.get_queryset()).values_list('labels__name', flat=True).distinct()

        return Response({
            'status': status,
            'category': category_type,
            'labels': labels,
        }, status=http_status_codes.HTTP_200_OK)


class RequestListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    #filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'ulid', 'description', 'status__name', 'requestor__username', 'supervisor__username', 'last_changed', 'labels__name']
    #filterset_class = RequestFilter
    pagination_class = LimitOffsetPagination


class RequestRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'ulid'


class StatisticView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        response_data = {
            'experiment_count': Experiment.objects.count(),
            'experiment_run_count': ExperimentRun.objects.count(),
            'environment_count': Environment.objects.count(),
            'testfunctionset_count': TestfunctionSet.objects.count(),
            'testfunction_count': TestFunction.objects.count(),
            'request_count': Request.objects.count(),
            'user_count': User.objects.count()
        }
        return Response(response_data, status=http_status_codes.HTTP_200_OK)


class ExperimentCheckView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        checks if experiment with given sha256 hash is published
        """
        experiment_sha256hash = request.query_params.get('sha256hash')
        if not experiment_sha256hash:
            return Response('No sha256 hash given', status=http_status_codes.HTTP_400_BAD_REQUEST)
        # check if experiment with given sha256 hash exists
        try:
            experiment = Experiment.objects.get(sha256hash=experiment_sha256hash)
        except Experiment.DoesNotExist:
            resp_data = {'published': None, 'publish_date': None, 'ulid': None, 'request_ulid': None}
            return Response(resp_data,
                            status=http_status_codes.HTTP_200_OK)
        # check if experiment is published
        if experiment.published:
            resp_data = {'published': True, 'publish_date': experiment.publish_date, 'ulid': experiment.ulid, 'request_ulid': None}
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)
        # check if request for experiment exists
        try:
            request = Request.objects.get(experiment=experiment)
            resp_data = {'published': False, 'publish_date': None, 'ulid': experiment.ulid, 'request_ulid': request.ulid}
        except Request.DoesNotExist:
            resp_data = {'published': False, 'publish_date': None, 'ulid': experiment.ulid, 'request_ulid': None}

        return Response(resp_data, status=http_status_codes.HTTP_200_OK)


class ExperimentCheckMultipleView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        checks if experiments with given sha256 hashes are published
        """
        # get sha256 hashes from request data
        experiment_sha256hashes = request.data.get('sha256hashes')
        if not experiment_sha256hashes:
            return Response('No sha256 hashes given', status=http_status_codes.HTTP_400_BAD_REQUEST)
        # check if experiment with given sha256 hash exists
        try:
            experiment_sha256hashes = experiment_sha256hashes.split(',')
            experiments = Experiment.objects.filter(sha256hash__in=experiment_sha256hashes)
        except Experiment.DoesNotExist:
            resp_data = {'published': None, 'publish_date': None, 'ulid': None, 'request_ulid': None}
            return Response(resp_data,
                            status=http_status_codes.HTTP_200_OK)
        # check if experiment is published
        resp_data = []
        for experiment in experiments:
            if experiment.published:
                resp_data.append({'published': True, 'publish_date': experiment.publish_date, 'ulid': experiment.ulid, 'request_ulid': None})
            else:
                # check if request for experiment exists
                try:
                    request = Request.objects.get(experiment=experiment)
                    resp_data.append({'published': False, 'publish_date': None, 'ulid': experiment.ulid, 'request_ulid': request.ulid})
                except Request.DoesNotExist:
                    resp_data.append({'published': False, 'publish_date': None, 'ulid': experiment.ulid, 'request_ulid': None})

        return Response(resp_data, status=http_status_codes.HTTP_200_OK)


class RequestCheckView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        checks if request with given ulid exists
        """
        resp_data = {
            'exists': False,
            'status': None,
        }

        request_ulid = request.query_params.get('ulid')
        if not request_ulid:
            return Response('No request ulid given', status=http_status_codes.HTTP_400_BAD_REQUEST)
        # check if request with given ulid exists
        try:
            request = Request.objects.get(ulid=request_ulid)
        except Request.DoesNotExist:
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)
        resp_data.update({
            'exists': True,
            'status': request.status.name,
        })
        return Response(resp_data, status=http_status_codes.HTTP_200_OK)


class ExperimentRunCheckView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
            checks if experiment run with given ulid exists
        """
        resp_data = {
            'exists': False,
        }

        experimentrun_ulid = request.query_params.get('ulid')
        if not experimentrun_ulid:
            return Response('No experiment run ulid given', status=http_status_codes.HTTP_400_BAD_REQUEST)
        # check if experiment run with given ulid exists
        try:
            experimentrun = ExperimentRun.objects.get(ulid=experimentrun_ulid)
        except ExperimentRun.DoesNotExist:
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)
        resp_data.update({
            'exists': True,
        })
        return Response(resp_data, status=http_status_codes.HTTP_200_OK)


class EnvironmentView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        downloads metadata of environment with given ulid
        """
        environment_ulid = request.query_params.get('ulid')
        if not environment_ulid:
            return Response('No environment ulid given', status=http_status_codes.HTTP_400_BAD_REQUEST)

        # check if environment with given ulid exists
        try:
            environment = Environment.objects.get(ulid=environment_ulid)
        except Environment.DoesNotExist:
            return Response(f'Environment with ulid {environment_ulid} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)

        if not environment.published:
            return Response(f'Environment with ulid {environment_ulid} is not published',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)

        serializer = EnvironmentSerializer(environment)
        # check if environment serialized data is valid
        if not serializer.is_valid():
            return Response(serializer.errors, status=http_status_codes.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=http_status_codes.HTTP_200_OK)


class EnvironmentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EnvironmentSerializer
    queryset = Environment.objects.filter(published=True).all()
    pagination_class = LimitOffsetPagination
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'box', 'os_info__distribution', 'os_info__version', 'os_info__arch', 'publisher__username', 'publish_date']


class EnvironmentFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Environment.objects.filter(published=True).all()
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'publisher__username', 'publish_date']

    def get(self, request, *args, **kwargs):
        return Response({}, status=http_status_codes.HTTP_200_OK)



def get_event_by_ulid(ulid: str):
    # Get all subclasses of Event
    event_subclasses = Event.__subclasses__()

    # List to store all events
    all_events = []

    # Query each subclass and combine the results
    for subclass in event_subclasses:
        events = subclass.objects.filter(ulid=ulid)
        all_events.extend(events)

    if len(all_events) == 1:
        return all_events[0]
    return None

class ExperimentRunDeleteView(generics.DestroyAPIView):
    permission_classes = [AllowAny]
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    lookup_field = 'ulid'


class ExperimentRunPublishView(generics.CreateAPIView):
    serializer_class = ExperimentRunCreateSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartJSONParser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        files = request.FILES
        data = request.data

        exp_ulid = data['experiment_ulid']
        env_ulid = data['environment_ulid']
        run_ulid = data['ulid']

        # check if experiment run already exists
        try:
            run = ExperimentRun.objects.get(ulid=run_ulid)
            return Response(f'Experiment run {run_ulid} already exists',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        except ExperimentRun.DoesNotExist:
            pass


        # get experiment for experiment run
        try:
            experiment = Experiment.objects.get(ulid=exp_ulid)
        except Experiment.DoesNotExist:
            return Response(f'Experiment with ulid {exp_ulid} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['experiment'] = experiment.ulid

        # check if experiment is published
        if not experiment.published:
            return Response(f'Experiment with ulid {experiment.ulid} is not published',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)

        try:
            environment = Environment.objects.get(ulid=data['environment_ulid'])
        except Environment.DoesNotExist:
            return Response(f'Environment with ulid {env_ulid} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['environment'] = environment.ulid

        # create or get Status
        try:
            status_object = Status.objects.get(id=data['status'])
        except Status.DoesNotExist:
            return Response(f'Status with id {data["status"]} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['status'] = status_object.id

        try:
            result_status_object = Status.objects.get(id=data['result_status'])
        except Status.DoesNotExist:
            return Response(f'Status with id {data["result_status"]} does not exist',
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        data['result_status'] = result_status_object.id

        data['published_by'] = request.user.gitea_user.id
        data['published_at'] = make_aware(datetime.now())
        if vagrantvm_log := files.get('adarevm_log'):
            data['adarevm_logfile'] = vagrantvm_log
        if installations_log := files.get('installations_log'):
            data['installations_logfile'] = installations_log
        if packagedump_log := files.get('packagedump_log'):
            data['packagedump_logfile'] = packagedump_log
        if networkdrives_log := files.get('networkdrives_log'):
            data['networkdrives_logfile'] = networkdrives_log
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        experiment_run = serializer.save()
        event_object_list = []
        for event in data['events']:
            event_object = get_event_by_ulid(event['ulid'])
            if event_object:
                return Response(f'Event with ulid {event["ulid"]} already exists', status=http_status_codes.HTTP_400_BAD_REQUEST)
            event_serializer = get_event_serializer(event['category'])(data=event)
            if not event_serializer.is_valid():
                return Response(event_serializer.errors, status=http_status_codes.HTTP_400_BAD_REQUEST)
            event_serializer.validated_data['run'] = experiment_run.ulid
            event_serializer.validated_data['status'] = event['status']
            if 'result' in event.keys():
                event_serializer.validated_data['result'] = event['result']
            if 'abstract_test_ulid' in event.keys():
                event_serializer.validated_data['abstracttest'] = event['abstract_test_ulid']
            event_object = event_serializer.save()
            event_object_list.append(event_object.ulid)
        data['events'] = event_object_list

        # todo: calculate result_status based on events and compare with given result_status if they do not match return error (and delete experiment run)
        non_empty_test_events = [event for event in data['events'] if event['category'] == 'test_event' and event['result']]



        return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)

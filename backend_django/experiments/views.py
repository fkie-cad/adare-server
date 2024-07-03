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
from django.contrib.auth.models import User
from helperfunctions.gitea import convert_gitea_internal_api_url_to_viewable_url

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
    search_fields = ['uuid', 'experiment__name', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentRunRetrieveView(generics.RetrieveAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'uuid'


class ExperimentListView(generics.ListAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.filter(published=True).all()
    permission_classes = [AllowAny]
    #filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    #filterset_class = ExperimentFilter
    search_fields = ['name', 'uuid', 'tags__name', 'description', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentRetrieveView(generics.RetrieveAPIView):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'uuid'


# class ExperimentByScenarioListView(generics.ListAPIView):
#     serializer_class = ExperimentSerializer
#     permission_classes = [AllowAny]
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
#     filterset_class = ExperimentFilter
#     # only for retrieve
#     lookup_field = 'uuid'
#
#     def get_queryset(self):
#         scenario_uuid = self.kwargs['uuid']
#         return Scenario.objects.get(uuid=scenario_uuid).experiments.filter(published=True).all()
#
#
# class ScenarioListView(generics.ListAPIView):
#     permission_classes = [AllowAny]
#     serializer_class = ScenarioSerializer
#     queryset = Scenario.objects.filter(published=True).all()
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ScenarioFilter
#     search_fields = ['name', 'uuid', 'tags__name', 'description', 'publisher__username', 'publish_date',
#                      'experiments__name']
#     pagination_class = LimitOffsetPagination


# class ScenarioFilterOptionsView(generics.RetrieveAPIView):
#     permission_classes = [AllowAny]
#     queryset = Scenario.objects.filter(published=True).all()
#     filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ScenarioFilter
#     search_fields = ['name', 'uuid', 'tags__name', 'description', 'publisher__username', 'publish_date',
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
    search_fields = ['name', 'uuid', 'tags__name', 'description', 'publisher__username', 'publish_date']

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
    search_fields = ['title', 'uuid', 'description', 'status__name', 'requestor__username', 'supervisor__username',
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
    search_fields = ['title', 'uuid', 'description', 'status__name', 'requestor__username', 'supervisor__username', 'last_changed', 'labels__name']
    #filterset_class = RequestFilter
    pagination_class = LimitOffsetPagination


class RequestRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = Request.objects.all()
    lookup_field = 'uuid'


class StatisticView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        response_data = {'experiment_count': Experiment.objects.count(),
                         #'scenario_count': Scenario.objects.count(),
                         'experiment_run_count': ExperimentRun.objects.count(),
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
            resp_data = {'published': None, 'publish_date': None, 'uuid': None, 'request_uuid': None}
            return Response(resp_data,
                            status=http_status_codes.HTTP_200_OK)
        # check if experiment is published
        if experiment.published:
            resp_data = {'published': True, 'publish_date': experiment.publish_date, 'uuid': experiment.uuid, 'request_uuid': None}
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)
        # check if request for experiment exists
        try:
            request = Request.objects.get(experiment=experiment)
            resp_data = {'published': False, 'publish_date': None, 'uuid': experiment.uuid, 'request_uuid': request.uuid}
        except Request.DoesNotExist:
            resp_data = {'published': False, 'publish_date': None, 'uuid': experiment.uuid, 'request_uuid': None}

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
            resp_data = {'published': None, 'publish_date': None, 'uuid': None, 'request_uuid': None}
            return Response(resp_data,
                            status=http_status_codes.HTTP_200_OK)
        # check if experiment is published
        resp_data = []
        for experiment in experiments:
            if experiment.published:
                resp_data.append({'published': True, 'publish_date': experiment.publish_date, 'uuid': experiment.uuid, 'request_uuid': None})
            else:
                # check if request for experiment exists
                try:
                    request = Request.objects.get(experiment=experiment)
                    resp_data.append({'published': False, 'publish_date': None, 'uuid': experiment.uuid, 'request_uuid': request.uuid})
                except Request.DoesNotExist:
                    resp_data.append({'published': False, 'publish_date': None, 'uuid': experiment.uuid, 'request_uuid': None})

        return Response(resp_data, status=http_status_codes.HTTP_200_OK)


class RequestCheckView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        checks if request with given uuid exists
        """
        resp_data = {
            'exists': False,
            'status': None,
        }

        request_uuid = request.query_params.get('uuid')
        if not request_uuid:
            return Response('No request uuid given', status=http_status_codes.HTTP_400_BAD_REQUEST)
        # check if request with given uuid exists
        try:
            request = Request.objects.get(uuid=request_uuid)
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
            checks if experiment run with given uuid exists
        """
        resp_data = {
            'exists': False,
        }

        experimentrun_uuid = request.query_params.get('uuid')
        if not experimentrun_uuid:
            return Response('No experiment run uuid given', status=http_status_codes.HTTP_400_BAD_REQUEST)
        # check if experiment run with given uuid exists
        try:
            experimentrun = ExperimentRun.objects.get(uuid=experimentrun_uuid)
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
        downloads metadata of environment with given uuid
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


# class ExperimentRunPublishView(generics.CreateAPIView):
#     serializer_class = ExperimentRunCreateSerializer
#     queryset = ExperimentRun.objects.all()
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartJSONParser]
#
#     def create(self, request, *args, **kwargs):
#         logfile = request.FILES.get('log_file')
#         data = request.data
#
#         exp_sha256hash = data['sha256hash']
#         experimentrun_uuid = data['uuid']
#         # experiment_uuid = data.pop('experiment_uuid')
#         status = data.pop('status')
#
#         # get experiment for experiment run
#         try:
#             experiment = Experiment.objects.get(sha256hash=exp_sha256hash)
#         except Experiment.DoesNotExist:
#             return Response(f'Experiment with hash {exp_sha256hash} does not exist',
#                             status=http_status_codes.HTTP_400_BAD_REQUEST)
#         data['experiment'] = experiment.uuid
#
#         # check if experiment is published
#         if not experiment.published:
#             return Response(f'Experiment with uuid {experiment.uuid} is not published',
#                             status=http_status_codes.HTTP_400_BAD_REQUEST)
#
#         # check if experiment run already exists
#         try:
#             ExperimentRun.objects.get(uuid=experimentrun_uuid)
#             return Response(f'Experiment run for experiment {experiment.uuid} already exists',
#                             status=http_status_codes.HTTP_400_BAD_REQUEST)
#         except ExperimentRun.DoesNotExist:
#             pass
#
#         # create or get Status
#         try:
#             status_object = Status.objects.get(name=status['name'])
#         except Status.DoesNotExist:
#             return Response(f'Status with name {status} does not exist',
#                             status=http_status_codes.HTTP_400_BAD_REQUEST)
#         data['status'] = status_object.id
#
#         tests = data.pop('tests')
#         test_object_list = []
#         for test in tests:
#             try:
#                 test_object = Test.objects.get(uuid=test['uuid'])
#             except Test.DoesNotExist:
#                 test_serializer = TestSerializer(data=test)
#                 test_serializer.is_valid(raise_exception=True)
#                 test_object = test_serializer.save()
#             test_object_list.append(test_object)
#
#         # check if all tests of the experiment are included in the experiment run and vice versa
#         uuid_tests = [test.abstracttest.uuid for test in test_object_list]
#         uuid_abstract_tests = [abstract_test.uuid for abstract_test in experiment.abstract_tests.all()]
#         if not set(uuid_abstract_tests).issubset(set(uuid_tests)):
#             return Response(f'Not all tests of experiment {experiment.uuid} are included in the experiment run',
#                             status=http_status_codes.HTTP_400_BAD_REQUEST)
#         if not set(uuid_tests).issubset(set(uuid_abstract_tests)):
#             return Response(f'Not all tests of experiment run {experimentrun_uuid} are included in the experiment',
#                             status=http_status_codes.HTTP_400_BAD_REQUEST)
#
#         data['publisher'] = request.user.id
#         data['publish_date'] = make_aware(datetime.now())
#         data['logfile'] = logfile
#         serializer = self.get_serializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         experiment_run = serializer.save()
#         experiment_run.tests.set(test_object_list)
#         return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)
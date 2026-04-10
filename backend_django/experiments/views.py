from datetime import datetime

import rest_framework.generics as generics
import rest_framework.status as http_status_codes
from django.db import transaction
from django.db.models import Count, Max, Q, Case, When, IntegerField, Sum
from django.utils.timezone import make_aware
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
import django_filters.rest_framework
from experiments.filters import ExperimentFilter, EnvironmentFilter, TestfunctionSetFilter, ExperimentRunFilter

from experiments.parsers import MultiPartJSONParser
from experiments.serializers import (
    ExperimentRunSerializer, ExperimentRunCreateSerializer,
    ExperimentSerializer, ExperimentViewableFilesSerializer,
    ExperimentMetadataSerializer,
    EnvironmentSerializer, EnvironmentMetadataSerializer,
    TestFunctionSetSerializer, TestFunctionSetMetadataSerializer,
    RequestSerializer,
    get_event_serializer,
)
from django.contrib.auth.models import User
from experiments.models import (
    Experiment, ExperimentRun, Environment, TestfunctionSet, TestFunction,
    Event, Status, Request, Label, Tag, TagScope,
)

class ExperimentRunListView(generics.ListAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.select_related(
        'published_by', 'experiment', 'environment', 'status', 'result_status'
    ).prefetch_related(
        'command_events', 'test_events', 'error_events',
        'gui_find_events', 'gui_click_events', 'gui_keypress_events', 'gui_idle_events',
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExperimentRunFilter
    search_fields = ['ulid', 'experiment__name', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentRunRetrieveView(generics.RetrieveAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.select_related(
        'published_by', 'experiment', 'environment', 'status', 'result_status'
    ).prefetch_related(
        'command_events', 'test_events', 'error_events',
        'gui_find_events', 'gui_click_events', 'gui_keypress_events', 'gui_idle_events',
    ).all()
    permission_classes = [AllowAny]
    lookup_field = 'ulid'


class ExperimentListView(generics.ListAPIView):
    serializer_class = ExperimentViewableFilesSerializer
    queryset = Experiment.objects.filter(published=True).select_related(
        'published_by', 'created_by'
    ).prefetch_related(
        'tags', 'tags__scope', 'environments', 'abstract_tests'
    ).annotate(
        successful_run_count=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='success')),
        failed_run_count=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='failed')),
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExperimentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentView(generics.RetrieveAPIView):
    serializer_class = ExperimentViewableFilesSerializer
    queryset = Experiment.objects.filter(published=True).select_related(
        'published_by', 'created_by'
    ).prefetch_related(
        'tags', 'environments', 'abstract_tests'
    ).all()
    permission_classes = [AllowAny]
    lookup_field = 'ulid'


class TestFunctionListView(generics.ListAPIView):
    serializer_class = TestFunctionSetSerializer
    queryset = TestfunctionSet.objects.filter(published=True).select_related(
        'published_by', 'created_by'
    ).prefetch_related(
        'testfunctions', 'testfunctions__possible_parameters', 'requirements', 'tags', 'tags__scope'
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TestfunctionSetFilter
    search_fields = ['name', 'ulid', 'description', 'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class ExperimentDownloadView(generics.RetrieveAPIView):
    serializer_class = ExperimentSerializer
    permission_classes = [AllowAny]
    queryset = Experiment.objects.filter(published=True).all()
    lookup_field = 'ulid'


class TestfunctionDownloadView(generics.RetrieveAPIView):
    serializer_class = TestFunctionSetSerializer
    permission_classes = [AllowAny]
    queryset = TestfunctionSet.objects.filter(published=True).select_related(
        'published_by', 'created_by'
    ).prefetch_related(
        'testfunctions', 'testfunctions__possible_parameters', 'requirements'
    ).all()
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




def _get_tags_by_scope(queryset, tag_field='tags'):
    """Helper to group tags by scope with counts for any entity queryset."""
    tag_counts = queryset.values(
        f'{tag_field}__name', f'{tag_field}__scope__name', f'{tag_field}__value'
    ).annotate(count=Count(f'{tag_field}__name')).exclude(
        **{f'{tag_field}__name': None}
    ).order_by(f'{tag_field}__scope__name', '-count')

    tags_by_scope = {}
    for entry in tag_counts:
        scope = entry[f'{tag_field}__scope__name'] or 'unscoped'
        if scope not in tags_by_scope:
            tags_by_scope[scope] = []
        tags_by_scope[scope].append({
            'value': entry[f'{tag_field}__value'],
            'name': entry[f'{tag_field}__name'],
            'count': entry['count'],
        })
    return tags_by_scope


class ExperimentFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Experiment.objects.filter(published=True).all()
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        # tags grouped by scope
        tags_by_scope = _get_tags_by_scope(qs)

        # flat tags list for backwards compatibility
        tags = qs.values_list('tags__name', flat=True).distinct()
        if len(tags) == 1 and tags[0] is None:
            tags = []

        # environments used by filtered experiments
        environments = list(
            qs.values_list('environments__name', flat=True).distinct().exclude(environments__name=None)
        )

        # run count stats (use result_status to match ExperimentListView annotations)
        max_success = qs.annotate(
            success_count=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='success'))
        ).aggregate(Max('success_count'))['success_count__max']

        max_failed = qs.annotate(
            failed_count=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='failed'))
        ).aggregate(Max('failed_count'))['failed_count__max']

        total_count = qs.annotate(
            total_count=Count('experiment_runs')
        ).aggregate(Max('total_count'))['total_count__max']

        return Response({
            'tags': tags,
            'tags_by_scope': tags_by_scope,
            'environments': environments,
            'max_success': max_success,
            'max_failed': max_failed,
            'total_count': total_count,
        }, status=http_status_codes.HTTP_200_OK)


class ExperimentDashboardView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Experiment.objects.filter(published=True).all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExperimentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        # Per-experiment run counts
        experiments = list(
            qs.annotate(
                successful_run_count=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='success')),
                failed_run_count=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='failed')),
            ).values('name', 'ulid', 'successful_run_count', 'failed_run_count')
            .order_by('-successful_run_count', 'name')
        )

        # Aggregate summary (directly on ExperimentRun to avoid annotation issues)
        experiment_ids = qs.values_list('ulid', flat=True)
        run_qs = ExperimentRun.objects.filter(experiment__ulid__in=experiment_ids)
        total_runs = run_qs.count()
        total_successful = run_qs.filter(result_status__name='success').count()
        total_failed = run_qs.filter(result_status__name='failed').count()

        summary = {
            'total_experiments': len(experiments),
            'total_runs': total_runs,
            'total_successful': total_successful,
            'total_failed': total_failed,
            'success_rate': round(total_successful / total_runs * 100, 1) if total_runs > 0 else 0,
        }

        return Response({
            'experiments': experiments,
            'summary': summary,
        }, status=http_status_codes.HTTP_200_OK)


class RequestFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Request.objects.all()
    search_fields = ['title', 'ulid', 'description', 'gitea_pr_status', 'requester__username', 'labels__name']

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
    queryset = Request.objects.select_related(
        'requester', 'objective'
    ).prefetch_related(
        'labels', 'reviewers', 'assignees'
    ).all()
    search_fields = ['title', 'ulid', 'description', 'gitea_pr_status', 'requester__username', 'labels__name']
    pagination_class = LimitOffsetPagination


class RequestRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = Request.objects.select_related(
        'requester', 'objective'
    ).prefetch_related(
        'labels', 'reviewers', 'assignees'
    ).all()
    lookup_field = 'ulid'


class StatisticView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        response_data = {
            'experiment_count': Experiment.objects.count(),
            'run_count': ExperimentRun.objects.count(),
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
            resp_data = {'published': None, 'published_at': None, 'ulid': None, 'request_ulid': None}
            return Response(resp_data,
                            status=http_status_codes.HTTP_200_OK)
        # check if experiment is published
        if experiment.published:
            resp_data = {'published': True, 'published_at': experiment.published_at, 'ulid': experiment.ulid, 'request_ulid': None}
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)
        # check if request for experiment exists
        from django.contrib.contenttypes.models import ContentType
        exp_ct = ContentType.objects.get_for_model(Experiment)
        try:
            req = Request.objects.get(objective=exp_ct, object_id=experiment.ulid)
            resp_data = {'published': False, 'published_at': None, 'ulid': experiment.ulid, 'request_ulid': req.ulid}
        except Request.DoesNotExist:
            resp_data = {'published': False, 'published_at': None, 'ulid': experiment.ulid, 'request_ulid': None}

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
            resp_data = {'published': None, 'published_at': None, 'ulid': None, 'request_ulid': None}
            return Response(resp_data,
                            status=http_status_codes.HTTP_200_OK)
        # check if experiment is published
        from django.contrib.contenttypes.models import ContentType
        exp_ct = ContentType.objects.get_for_model(Experiment)
        resp_data = []
        for experiment in experiments:
            if experiment.published:
                resp_data.append({'published': True, 'published_at': experiment.published_at, 'ulid': experiment.ulid, 'request_ulid': None})
            else:
                # check if request for experiment exists
                try:
                    req = Request.objects.get(objective=exp_ct, object_id=experiment.ulid)
                    resp_data.append({'published': False, 'published_at': None, 'ulid': experiment.ulid, 'request_ulid': req.ulid})
                except Request.DoesNotExist:
                    resp_data.append({'published': False, 'published_at': None, 'ulid': experiment.ulid, 'request_ulid': None})

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
            'status': request.gitea_pr_status,
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
    serializer_class = EnvironmentSerializer
    queryset = Environment.objects.filter(published=True).select_related(
        'os_info', 'published_by', 'created_by'
    ).prefetch_related(
        'tags', 'tags__scope', 'post_setup_installations'
    ).all()
    permission_classes = [AllowAny]
    lookup_field = 'name'


class TestfunctionFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = TestfunctionSet.objects.filter(published=True).all()
    search_fields = ['name', 'ulid', 'description', 'published_by__username', 'published_at']

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        tags_by_scope = _get_tags_by_scope(qs)

        return Response({
            'tags_by_scope': tags_by_scope,
        }, status=http_status_codes.HTTP_200_OK)


class EnvironmentListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EnvironmentSerializer
    queryset = Environment.objects.filter(published=True).select_related(
        'os_info', 'published_by', 'created_by'
    ).prefetch_related(
        'tags', 'tags__scope', 'post_setup_installations'
    ).all()
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EnvironmentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'vagrantbox',
                     'os_info__distribution', 'os_info__version', 'os_info__architecture',
                     'published_by__username', 'published_at']
    pagination_class = LimitOffsetPagination


class EnvironmentFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Environment.objects.filter(published=True).all()
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        tags_by_scope = _get_tags_by_scope(qs)

        # OS options
        os_values = list(
            qs.values_list('os_info__os', flat=True).distinct().exclude(os_info__os=None)
        )
        distribution_values = list(
            qs.values_list('os_info__distribution', flat=True).distinct().exclude(os_info__distribution=None)
        )

        return Response({
            'tags_by_scope': tags_by_scope,
            'os': os_values,
            'distributions': distribution_values,
        }, status=http_status_codes.HTTP_200_OK)



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
        # non_empty_test_events = [event for event in data['events'] if event['category'] == 'test_event' and event['result']]



        return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)

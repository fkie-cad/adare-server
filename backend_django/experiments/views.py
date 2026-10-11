from collections import defaultdict

import rest_framework.generics as generics
import rest_framework.status as http_status_codes
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q
from django.utils import timezone
from adare.pagination import DefaultLimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
import django_filters.rest_framework
from experiments.filters import ExperimentFilter, EnvironmentFilter, TestfunctionSetFilter, ExperimentRunFilter

from experiments.parsers import MultiPartJSONParser
from experiments.serializers import (
    ExperimentRunSerializer, ExperimentRunListSerializer, ExperimentRunCreateSerializer,
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
    TestEvent, ErrorEvent, ActionEvent, TestParameterEntry, AbstractTest,
)

_experiment_run_queryset = ExperimentRun.objects.select_related(
    'published_by', 'experiment', 'environment', 'status', 'result_status'
).order_by('-published_at', 'pk')

# The run detail renders every event: TestEventSerializer walks
# status, result.status and the full AbstractTestSerializer tree
# (testfunction -> set name / possible_parameters, parameters -> parameter,
# tools); error/action events only add status. Without these the detail
# view issued several queries per event.
_experiment_run_detail_queryset = _experiment_run_queryset.prefetch_related(
    Prefetch('test_events', queryset=TestEvent.objects.select_related(
        'status', 'result__status', 'abstracttest__testfunction__testfunction_set',
    ).prefetch_related(
        Prefetch('abstracttest__parameters', queryset=TestParameterEntry.objects.select_related('parameter')),
        'abstracttest__tools',
        'abstracttest__testfunction__possible_parameters',
    )),
    Prefetch('error_events', queryset=ErrorEvent.objects.select_related('status')),
    Prefetch('action_events', queryset=ActionEvent.objects.select_related('status')),
)


class ExperimentRunListView(generics.ListAPIView):
    # slim serializer: no `events` (the list page never shows them, and
    # rendering them cost a query fan-out per event per run)
    serializer_class = ExperimentRunListSerializer
    queryset = _experiment_run_queryset
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExperimentRunFilter
    search_fields = ['ulid', 'experiment__name', 'published_by__username', 'published_at']
    pagination_class = DefaultLimitOffsetPagination


class ExperimentRunRetrieveView(generics.RetrieveAPIView):
    serializer_class = ExperimentRunSerializer
    queryset = _experiment_run_detail_queryset
    permission_classes = [AllowAny]
    lookup_field = 'ulid'


def _scoped_tags_prefetch(lookup='tags'):
    return Prefetch(lookup, queryset=Tag.objects.select_related('scope'))


# Everything ExperimentSerializer renders below the experiment row itself:
# AbstractTestSerializer (testfunction -> set name / possible_parameters,
# parameters -> parameter, tools), TagSerializer (scope) and the nested
# EnvironmentSerializer (os_info, recipe, users, scoped tags, post-setup
# installations). Shared by the experiment list/detail and the request views.
EXPERIMENT_PREFETCHES = (
    Prefetch('abstract_tests', queryset=AbstractTest.objects.select_related(
        'testfunction__testfunction_set',
    ).prefetch_related(
        Prefetch('parameters', queryset=TestParameterEntry.objects.select_related('parameter')),
        'tools',
        'testfunction__possible_parameters',
    )),
    _scoped_tags_prefetch(),
    Prefetch('environments', queryset=Environment.objects.select_related(
        'os_info', 'recipe', 'published_by', 'created_by',
    ).prefetch_related(
        _scoped_tags_prefetch(), 'post_setup_installations',
    )),
)

# run counts read by ExperimentSerializer.get_run_counts; without them it falls
# back to two COUNT queries per experiment
RUN_COUNT_ANNOTATIONS = {
    'successful_run_count': Count('experiment_runs', filter=Q(experiment_runs__result_status__name='success')),
    'failed_run_count': Count('experiment_runs', filter=Q(experiment_runs__result_status__name='failed')),
}

_published_experiment_queryset = Experiment.objects.filter(published=True).select_related(
    'published_by', 'created_by'
).prefetch_related(
    *EXPERIMENT_PREFETCHES
).annotate(**RUN_COUNT_ANNOTATIONS).order_by('-published_at', 'pk')


class ExperimentListView(generics.ListAPIView):
    serializer_class = ExperimentViewableFilesSerializer
    queryset = _published_experiment_queryset
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExperimentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'published_by__username', 'published_at']
    pagination_class = DefaultLimitOffsetPagination


class ExperimentView(generics.RetrieveAPIView):
    serializer_class = ExperimentViewableFilesSerializer
    queryset = _published_experiment_queryset
    permission_classes = [AllowAny]
    lookup_field = 'ulid'


class TestFunctionListView(generics.ListAPIView):
    serializer_class = TestFunctionSetSerializer
    queryset = TestfunctionSet.objects.filter(published=True, is_current=True).select_related(
        'published_by', 'created_by'
    ).prefetch_related(
        'testfunctions', 'testfunctions__possible_parameters', 'requirements', 'tags', 'tags__scope'
    ).order_by('-published_at', 'pk')
    permission_classes = [AllowAny]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TestfunctionSetFilter
    search_fields = ['name', 'ulid', 'description', 'published_by__username', 'published_at']
    pagination_class = DefaultLimitOffsetPagination


class ExperimentDownloadView(generics.RetrieveAPIView):
    serializer_class = ExperimentSerializer
    permission_classes = [AllowAny]
    queryset = _published_experiment_queryset
    lookup_field = 'ulid'


class TestfunctionDownloadView(generics.RetrieveAPIView):
    serializer_class = TestFunctionSetSerializer
    permission_classes = [AllowAny]
    queryset = TestfunctionSet.objects.filter(published=True, is_current=True).select_related(
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
    lookup_field = 'sha256playbook'
    lookup_url_kwarg = 'sha256hash'


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


def _request_object_querysets():
    """Per objective model: the queryset GenericRequestObjectSerializer needs.

    Each mirrors what the nested Experiment/Environment/TestFunctionSet
    serializer touches, so rendering a request's `object` costs no extra
    queries.
    """
    return {
        Experiment: Experiment.objects.select_related(
            'published_by', 'created_by'
        ).prefetch_related(*EXPERIMENT_PREFETCHES).annotate(**RUN_COUNT_ANNOTATIONS),
        Environment: Environment.objects.select_related(
            'os_info', 'recipe', 'published_by', 'created_by'
        ).prefetch_related(_scoped_tags_prefetch(), 'post_setup_installations'),
        TestfunctionSet: TestfunctionSet.objects.select_related(
            'published_by', 'created_by'
        ).prefetch_related(
            'testfunctions', 'testfunctions__possible_parameters', 'requirements', _scoped_tags_prefetch()
        ),
    }


def _attach_request_objects(requests):
    """Resolve `Request.object` for many requests with one query per objective model.

    `object` is a GenericForeignKey, so plain prefetch_related('object') can
    fetch the targets but cannot prefetch *their* relations (they differ per
    model; per-model GenericPrefetch only arrives in Django 5). Fetch each
    model's targets with its full queryset instead and seed the GFK cache. A
    target that no longer exists is cached as None, exactly what the lazy GFK
    lookup would return.
    """
    object_field = Request._meta.get_field('object')
    querysets = _request_object_querysets()
    ids_by_model = defaultdict(set)
    for req in requests:
        model = req.objective.model_class()
        if model in querysets:
            ids_by_model[model].add(req.object_id)

    resolved = {}
    for model, ids in ids_by_model.items():
        for obj in querysets[model].filter(pk__in=ids):
            resolved[(model, obj.pk)] = obj

    for req in requests:
        model = req.objective.model_class()
        if model in querysets:
            object_field.set_cached_value(req, resolved.get((model, req.object_id)))


_request_queryset = Request.objects.select_related(
    'requester', 'objective'
).prefetch_related(
    'labels', 'reviewers', 'assignees'
).order_by('-creation_date', 'pk')


class RequestListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = _request_queryset
    search_fields = ['title', 'ulid', 'description', 'gitea_pr_status', 'requester__username', 'labels__name']
    pagination_class = DefaultLimitOffsetPagination

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is not None:
            _attach_request_objects(page)
        return page


class RequestRetrieveView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = _request_queryset
    lookup_field = 'ulid'

    def get_object(self):
        request_obj = super().get_object()
        _attach_request_objects([request_obj])
        return request_obj


class StatisticView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        response_data = {
            'experiment_count': Experiment.objects.count(),
            'run_count': ExperimentRun.objects.count(),
            'environment_count': Environment.objects.count(),
            'testfunctionset_count': TestfunctionSet.objects.filter(is_current=True).count(),
            'testfunction_count': TestFunction.objects.count(),
            'request_count': Request.objects.count(),
            'user_count': User.objects.count()
        }
        return Response(response_data, status=http_status_codes.HTTP_200_OK)


class ExperimentCheckView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        checks if experiment with given sha256 hash or ULID is published
        """
        # Support ULID-based lookup alongside sha256hash
        experiment_ulid = request.query_params.get('ulid')
        if experiment_ulid:
            try:
                experiment = Experiment.objects.get(ulid=experiment_ulid)
            except Experiment.DoesNotExist:
                resp_data = {'published': None, 'published_at': None, 'ulid': None, 'request_ulid': None}
                return Response(resp_data, status=http_status_codes.HTTP_200_OK)
            resp_data = {
                'published': experiment.published,
                'published_at': experiment.published_at,
                'ulid': experiment.ulid,
                'request_ulid': None,
            }
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)

        experiment_sha256hash = request.query_params.get('sha256hash')
        if not experiment_sha256hash:
            return Response('No sha256 hash or ulid given', status=http_status_codes.HTTP_400_BAD_REQUEST)
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
            request_obj = Request.objects.get(ulid=request_ulid)
        except Request.DoesNotExist:
            return Response(resp_data, status=http_status_codes.HTTP_200_OK)
        resp_data.update({
            'exists': True,
            'status': request_obj.gitea_pr_status,
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
        'os_info', 'recipe', 'published_by', 'created_by'
    ).prefetch_related(
        'tags', 'tags__scope', 'post_setup_installations'
    ).all()
    permission_classes = [AllowAny]
    lookup_field = 'name'


class TestfunctionFilterOptionsView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = TestfunctionSet.objects.filter(published=True, is_current=True).all()
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
        'os_info', 'recipe', 'published_by', 'created_by'
    ).prefetch_related(
        'tags', 'tags__scope', 'post_setup_installations'
    ).order_by('-published_at', 'pk')
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EnvironmentFilter
    search_fields = ['name', 'ulid', 'tags__name', 'description', 'vagrantbox',
                     'os_info__distribution', 'os_info__version', 'os_info__architecture',
                     'published_by__username', 'published_at']
    pagination_class = DefaultLimitOffsetPagination


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
    for model in (TestEvent, ErrorEvent, ActionEvent):
        try:
            return model.objects.get(ulid=ulid)
        except model.DoesNotExist:
            continue
    return None


class EventIngestError(Exception):
    """Raised to abort event ingestion and roll back the enclosing transaction.

    Carries the same (data, status_code) pair the view would otherwise have
    returned directly as a Response, so create()'s except clause can rebuild
    the identical error response for the client.
    """

    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code
        super().__init__(data.get('message', 'Event ingestion failed.'))

class ExperimentRunDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExperimentRunSerializer
    queryset = ExperimentRun.objects.all()
    lookup_field = 'ulid'


class ExperimentRunPublishView(generics.CreateAPIView):
    serializer_class = ExperimentRunCreateSerializer
    queryset = ExperimentRun.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartJSONParser]

    @staticmethod
    def _validate_experiment(exp_ulid):
        """Return (Experiment, None) or (None, error Response)."""
        if not exp_ulid:
            return None, Response(
                {'error': 'missing_field', 'message': 'Missing required field: experiment_ulid'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        try:
            experiment = Experiment.objects.get(ulid=exp_ulid)
        except Experiment.DoesNotExist:
            return None, Response(
                {'error': 'experiment_not_found', 'message': f'Experiment {exp_ulid} does not exist.'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        if not experiment.published:
            return None, Response(
                {'error': 'experiment_not_published', 'message': f'Experiment {exp_ulid} is not published.'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        return experiment, None

    @staticmethod
    def _validate_environment(env_ulid):
        """Return (Environment, None) or (None, error Response)."""
        if not env_ulid:
            return None, Response(
                {'error': 'missing_field', 'message': 'Missing required field: environment_ulid'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        try:
            environment = Environment.objects.get(ulid=env_ulid)
        except Environment.DoesNotExist:
            return None, Response(
                {'error': 'environment_not_found', 'message': f'Environment {env_ulid} does not exist.'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        return environment, None

    @staticmethod
    def _resolve_status(name, field_label):
        """Return (Status, None) or (None, error Response)."""
        try:
            return Status.objects.get(name=name), None
        except Status.DoesNotExist:
            return None, Response(
                {'error': 'validation_error', 'message': f'{field_label} "{name}" not found.'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )

    @staticmethod
    def _process_events(data, experiment_run):
        """Process event list and attach to run. Raises EventIngestError on failure."""
        default_group_counter = 0
        for event in data.get('events', []):
            if get_event_by_ulid(event.get('ulid', '')):
                raise EventIngestError(
                    {'error': 'event_validation_error',
                     'message': f'Event {event["ulid"]} already exists.'},
                    http_status_codes.HTTP_400_BAD_REQUEST,
                )

            if not event.get('status'):
                event['status'] = 'finished'
            if not event.get('event_group_id'):
                event['event_group_id'] = str(default_group_counter)
                default_group_counter += 1

            category = event.get('category', '')
            event_serializer = get_event_serializer(category)(data=event)
            if not event_serializer.is_valid():
                raise EventIngestError(
                    {'error': 'event_validation_error',
                     'message': f'Validation failed for event {event.get("ulid", "?")}.',
                     'details': event_serializer.errors},
                    http_status_codes.HTTP_400_BAD_REQUEST,
                )
            event_serializer.validated_data['run'] = experiment_run.ulid
            event_serializer.validated_data['status'] = event['status']
            if 'result' in event:
                event_serializer.validated_data['result'] = event['result']
            if 'abstract_test_ulid' in event:
                event_serializer.validated_data['abstracttest'] = event['abstract_test_ulid']
            event_serializer.save()

    @staticmethod
    def _save_run_and_events(serializer, data):
        """Save the run and its events as a single all-or-nothing transaction.

        Deliberately scoped to just this `with` block (not the whole view) so
        that an EventIngestError raised by _process_events propagates out of
        the block *before* any except clause can swallow it — that's what
        makes transaction.atomic actually roll back the run row along with
        every event saved before the failure.
        """
        with transaction.atomic():
            experiment_run = serializer.save()
            ExperimentRunPublishView._process_events(data, experiment_run)
        return experiment_run

    def create(self, request, *args, **kwargs):
        files = request.FILES
        data = request.data

        run_ulid = data.get('ulid')
        content_hash = data.get('content_hash', '')

        if not run_ulid:
            return Response(
                {'error': 'missing_field', 'message': 'Missing required field: ulid'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )

        # Idempotent: return existing run if already uploaded
        try:
            existing_run = ExperimentRun.objects.get(ulid=run_ulid)
            serializer = ExperimentRunSerializer(existing_run)
            return Response(serializer.data, status=http_status_codes.HTTP_200_OK)
        except ExperimentRun.DoesNotExist:
            pass

        # Content hash dedup
        if content_hash:
            dup = ExperimentRun.objects.filter(content_hash=content_hash).first()
            if dup:
                return Response(
                    {'error': 'content_duplicate', 'message': 'A run with identical content already exists.',
                     'existing_ulid': dup.ulid},
                    status=http_status_codes.HTTP_409_CONFLICT,
                )

        # Validate experiment
        experiment, err = self._validate_experiment(data.get('experiment_ulid'))
        if err:
            return err
        data['experiment'] = experiment.ulid

        # Validate environment
        environment, err = self._validate_environment(data.get('environment_ulid'))
        if err:
            return err
        data['environment'] = environment.ulid

        # Resolve statuses
        status_obj, err = self._resolve_status(data.get('status', ''), 'Status')
        if err:
            return err
        data['status'] = status_obj.id

        result_status_obj, err = self._resolve_status(data.get('result_status', ''), 'Result status')
        if err:
            return err
        data['result_status'] = result_status_obj.id

        # Resolve Gitea user
        try:
            data['published_by'] = request.user.gitea_user.id
        except AttributeError:
            return Response(
                {'error': 'gitea_user_not_found', 'message': 'Your account has no linked Gitea user.'},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        data['published_at'] = timezone.now()
        data['content_hash'] = content_hash

        # Attach log files (all optional)
        if vagrantvm_log := files.get('adarevm_log'):
            data['adarevm_logfile'] = vagrantvm_log
        if installations_log := files.get('installations_log'):
            data['installations_logfile'] = installations_log
        if packagedump_log := files.get('packagedump_log'):
            data['packagedump_logfile'] = packagedump_log
        if networkdrives_log := files.get('networkdrives_log'):
            data['networkdrives_logfile'] = networkdrives_log

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(
                {'error': 'validation_error', 'message': 'Run validation failed.',
                 'details': serializer.errors},
                status=http_status_codes.HTTP_400_BAD_REQUEST,
            )
        # Save the run and its events atomically. Raising (rather than
        # returning) an error from within _process_events lets the atomic
        # block in _save_run_and_events roll back the run + every event
        # saved so far, instead of leaving a partially-ingested run committed.
        try:
            self._save_run_and_events(serializer, data)
        except EventIngestError as exc:
            return Response(exc.data, status=exc.status_code)

        return Response(serializer.data, status=http_status_codes.HTTP_201_CREATED)

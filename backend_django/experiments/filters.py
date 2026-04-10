from django_filters import rest_framework as filters
from experiments.models import Experiment, Environment, TestfunctionSet, TestFunction, Request, Tag, Label, ExperimentRun
from django.db.models import Q, Count
from datetime import datetime




class ExperimentFilter(filters.FilterSet):
    ulid_contains = filters.CharFilter(field_name='ulid', lookup_expr='contains')
    name_contains = filters.CharFilter(field_name='name', lookup_expr='contains')
    description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
    publisher_name_contains = filters.CharFilter(field_name='published_by', lookup_expr='username__contains')
    publish_date_contains = filters.CharFilter(field_name='published_at', lookup_expr='contains')
    tags_contains = filters.CharFilter(field_name='tags', lookup_expr='name__contains')
    min_runcount_pos = filters.NumberFilter(method='runcount_pos_filter')
    min_runcount_neg = filters.NumberFilter(method='runcount_neg_filter')
    min_runcount = filters.NumberFilter(method='runcount_filter')

    latest_experiment_run_before = filters.CharFilter(method='latest_experiment_run_filter_before')
    latest_experiment_run_after = filters.CharFilter(method='latest_experiment_run_filter_after')

    # used for filtering by predefined entries
    tags_mc = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name',
                                                queryset=Tag.objects.all())

    # scoped tag filter: accepts comma-separated scope:value pairs e.g. tool:Autopsy,goal:tool-test
    tags_scoped = filters.CharFilter(method='tags_scoped_filter')

    # filter experiments by environment name
    environment_mc = filters.CharFilter(method='environment_mc_filter')

    # filter experiments by testfunction set name
    testfunction_set = filters.CharFilter(method='testfunction_set_filter')

    def tags_scoped_filter(self, queryset, name, value):
        tag_names = [t.strip() for t in value.split(',') if t.strip()]
        for tag_name in tag_names:
            queryset = queryset.filter(tags__name=tag_name)
        return queryset.distinct()

    def environment_mc_filter(self, queryset, name, value):
        env_names = [e.strip() for e in value.split(',') if e.strip()]
        return queryset.filter(environments__name__in=env_names).distinct()

    def testfunction_set_filter(self, queryset, name, value):
        return queryset.filter(
            abstract_tests__testfunction__testfunction_set__name=value
        ).distinct()

    def os_info_filter(self, queryset, name, value):
        return queryset.filter(
            Q(os_info__os__icontains=value) |
            Q(os_info__distribution__icontains=value) |
            Q(os_info__version__icontains=value) |
            Q(os_info__language__icontains=value) |
            Q(os_info__architecture__icontains=value) |
            Q(os_info__details__icontains=value)
        )

    def runcount_pos_filter(self, queryset, name, value):
        return queryset.annotate(
            runcount=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='success'))
        ).filter(runcount__gte=value)

    def runcount_neg_filter(self, queryset, name, value):
        return queryset.annotate(
            runcount=Count('experiment_runs', filter=Q(experiment_runs__result_status__name='failed'))
        ).filter(runcount__gte=value)

    def runcount_filter(self, queryset, name, value):
        # count the number of experiment runs for each experiment that have the status success
        # and filter out those that have more than the specified number
        return queryset.annotate(
            runcount=Count('experiment_runs')
        ).filter(runcount__gte=value)

    def latest_experiment_run_filter_after(self, queryset, name, value):
        # split value into date and whether to look for negative, positive or all experiment runs
        status = None
        if ',' in value:
            value, status = value.split(',')
        # cast value to datetime
        value = datetime.strptime(value, '%Y-%m-%d')

        # get all experiments with at least one experiment run newer than the specified date
        # exclude experiments with no experiment runs
        if status == 'success' or status == 'failed':
            return queryset.filter(
                Q(experiment_runs__timestamp_end__gt=value) &
                Q(experiment_runs__status__name=status) &
                Q(experiment_runs__isnull=False)
            ).distinct()

        return queryset.filter(
            Q(experiment_runs__timestamp_end__gt=value) &
            Q(experiment_runs__isnull=False)
        ).distinct()


    def latest_experiment_run_filter_before(self, queryset, name, value):
        # split value into date and whether to look for negative, positive or all experiment runs
        status = None
        if ',' in value:
            value, status = value.split(',')
        # cast value to datetime
        value = datetime.strptime(value, '%Y-%m-%d')

        # filter out all experiments with all experiment runs newer than the specified date
        # exclude experiments with no experiment runs
        if status == 'success' or status == 'failed':
            return queryset.exclude(
                Q(experiment_runs__timestamp_end__gt=value)
            ).filter(
                Q(experiment_runs__status__name=status) &
                Q(experiment_runs__isnull=False)
            ).distinct()
        return queryset.exclude(
            Q(experiment_runs__timestamp_end__gt=value)
        ).filter(
            Q(experiment_runs__isnull=False)
        ).distinct()

    class Meta:
        model = Experiment
        fields = [
            'ulid',
            'name',
            'description',
            'published_by',
            'published_at',
            'tags',
        ]
#
#
# class RequestFilter(filters.FilterSet):
#     ulid_contains = filters.CharFilter(field_name='ulid', lookup_expr='contains')
#     description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
#     last_changed_contains = filters.CharFilter(field_name='last_change_date', lookup_expr='contains')
#     request_creation_date_contains = filters.CharFilter(field_name='creation_date', lookup_expr='contains')
#     requestor_contains = filters.CharFilter(field_name='requester', lookup_expr='username__contains')
#     supervisor_assigned_by_contains = filters.CharFilter(field_name='supervisor_assigned_by',
#                                                          lookup_expr='username__contains')
#     labels_contains = filters.CharFilter(field_name='labels', lookup_expr='name__contains')
#     username = filters.CharFilter(method='user_filter')
#
#     # used for filtering by predefined entries
#     # status_mc = filters.ModelMultipleChoiceFilter(field_name='status__name', to_field_name='name',
#     #                                               queryset=RequestStatus.objects.all())
#     category_mc = filters.MultipleChoiceFilter(method='category_filter',
#                                                choices=[('experiment', 'experiment'), ('scenario', 'scenario')])
#     labels_mc = filters.ModelMultipleChoiceFilter(field_name='labels__name', to_field_name='name',
#                                                   queryset=Label.objects.all())
#
#     last_changed_from = filters.DateFilter(field_name='last_change_date', lookup_expr='date__gte')
#     last_changed_to = filters.DateFilter(field_name='last_change_date', lookup_expr='date__lte')
#
#     def user_filter(self, queryset, name, value):
#         return queryset.filter(
#             Q(requestor__username__icontains=value) |
#             Q(supervisor__username__icontains=value)
#         )
#
#     def category_filter(self, queryset, name, value):
#         for v in value:
#             if v == 'experiment':
#                 queryset = queryset.filter(experiment__isnull=False)
#             elif v == 'scenario':
#                 queryset = queryset.filter(scenario__isnull=False)
#         return queryset
#
#     class Meta:
#         model = Request
#         fields = [
#             'ulid',
#             'description',
#         ]
#
#
class EnvironmentFilter(filters.FilterSet):
    tags_mc = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name',
                                                queryset=Tag.objects.all())
    tags_scoped = filters.CharFilter(method='tags_scoped_filter')
    os_mc = filters.CharFilter(method='os_mc_filter')

    def tags_scoped_filter(self, queryset, name, value):
        tag_names = [t.strip() for t in value.split(',') if t.strip()]
        for tag_name in tag_names:
            queryset = queryset.filter(tags__name=tag_name)
        return queryset.distinct()

    def os_mc_filter(self, queryset, name, value):
        os_values = [o.strip() for o in value.split(',') if o.strip()]
        return queryset.filter(
            Q(os_info__os__in=os_values) | Q(os_info__distribution__in=os_values)
        ).distinct()

    class Meta:
        model = Environment
        fields = [
            'name',
            'tags',
        ]


class TestfunctionSetFilter(filters.FilterSet):
    tags_mc = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name',
                                                queryset=Tag.objects.all())
    tags_scoped = filters.CharFilter(method='tags_scoped_filter')

    def tags_scoped_filter(self, queryset, name, value):
        tag_names = [t.strip() for t in value.split(',') if t.strip()]
        for tag_name in tag_names:
            queryset = queryset.filter(tags__name=tag_name)
        return queryset.distinct()

    class Meta:
        model = TestfunctionSet
        fields = [
            'name',
            'tags',
        ]


class ExperimentRunFilter(filters.FilterSet):
    ulid_contains = filters.CharFilter(field_name='ulid', lookup_expr='contains')

    class Meta:
        model = ExperimentRun
        fields = [
            'ulid',
        ]


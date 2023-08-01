from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from experiments.models import Scenario, Experiment, TestFunction, Request, Tag, RequestStatus, Label
from django.db.models import Q


class ScenarioFilter(filters.FilterSet):
    uuid_contains = filters.CharFilter(field_name='uuid', lookup_expr='contains')
    name_contains = filters.CharFilter(field_name='name', lookup_expr='contains')
    description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
    publisher_name_contains = filters.CharFilter(field_name='publisher', lookup_expr='username__contains')
    publish_date_contains = filters.CharFilter(field_name='publish_date', lookup_expr='contains')
    tags_contains = filters.CharFilter(field_name='tags', lookup_expr='name__contains')
    experiments_contains = filters.CharFilter(field_name='experiments', lookup_expr='contains')

    # used for filtering by predefined entries
    tags_mc = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name', queryset=Tag.objects.all())

    class Meta:
        model = Scenario
        fields = [
            'uuid',
            'name',
            'description',
            'publisher',
            'publish_date',
            'tags',
            'experiments',
        ]


class ExperimentFilter(filters.FilterSet):
    uuid_contains = filters.CharFilter(field_name='uuid', lookup_expr='contains')
    name_contains = filters.CharFilter(field_name='name', lookup_expr='contains')
    os_info_contains = filters.CharFilter(field_name='os_info', method='os_info_filter')
    description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
    publisher_contains = filters.CharFilter(field_name='publisher', lookup_expr='username__contains')
    publish_date_contains = filters.CharFilter(field_name='publish_date', lookup_expr='contains')
    tags_contains = filters.CharFilter(field_name='tags', lookup_expr='name__contains')

    # used for filtering by predefined entries
    tags_mc = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name', queryset=Tag.objects.all())

    def os_info_filter(self, queryset, name, value):
        return queryset.filter(
            Q(os_info__os__icontains=value) |
            Q(os_info__distribution__icontains=value) |
            Q(os_info__version__icontains=value) |
            Q(os_info__language__icontains=value) |
            Q(os_info__architecture__icontains=value) |
            Q(os_info__details__icontains=value)
        )

    class Meta:
        model = Experiment
        fields = [
            'uuid',
            'name',
            'description',
            'publisher',
            'publish_date',
            'tags',
        ]


class RequestFilter(filters.FilterSet):
    uuid_contains = filters.CharFilter(field_name='uuid', lookup_expr='contains')
    description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
    last_changed_contains = filters.CharFilter(field_name='last_changed', lookup_expr='contains')
    request_creation_date_contains = filters.CharFilter(field_name='request_creation_date', lookup_expr='contains')
    requestor_contains = filters.CharFilter(field_name='requestor', lookup_expr='username__contains')
    supervisor_contains = filters.CharFilter(field_name='supervisor', lookup_expr='username__contains')
    supervisor_assigned_by_contains = filters.CharFilter(field_name='supervisor_assigned_by', lookup_expr='username__contains')
    labels_contains = filters.CharFilter(field_name='labels', lookup_expr='name__contains')

    # used for filtering by predefined entries
    status_mc = filters.ModelMultipleChoiceFilter(field_name='status__name', to_field_name='name', queryset=RequestStatus.objects.all())
    category_mc = filters.MultipleChoiceFilter(method='category_filter', choices=[('experiment', 'experiment'), ('scenario', 'scenario')])
    labels_mc = filters.ModelMultipleChoiceFilter(field_name='labels__name', to_field_name='name', queryset=Label.objects.all())

    def category_filter(self, queryset, name, value):
        for v in value:
            if v == 'experiment':
                queryset = queryset.filter(experiment__isnull=False)
            elif v == 'scenario':
                queryset = queryset.filter(scenario__isnull=False)
        return queryset



    class Meta:
        model = Request
        fields = [
            'uuid',
            'description',
        ]




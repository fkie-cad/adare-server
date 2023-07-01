from django_filters import rest_framework as filters

from experiments.models import Scenario, Experiment


class ScenarioFilter(filters.FilterSet):
    uuid_contains = filters.CharFilter(field_name='uuid', lookup_expr='contains')
    name_contains = filters.CharFilter(field_name='name', lookup_expr='contains')
    description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
    publisher_contains = filters.CharFilter(field_name='publisher', lookup_expr='username__contains')
    publish_date_contains = filters.CharFilter(field_name='publish_date', lookup_expr='contains')
    tags_contains = filters.CharFilter(field_name='tags', lookup_expr='name__contains')
    experiments_contains = filters.CharFilter(field_name='experiments', lookup_expr='contains')

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
    description_contains = filters.CharFilter(field_name='description', lookup_expr='contains')
    publisher_contains = filters.CharFilter(field_name='publisher', lookup_expr='username__contains')
    publish_date_contains = filters.CharFilter(field_name='publish_date', lookup_expr='contains')
    tags_contains = filters.CharFilter(field_name='tags', lookup_expr='name__contains')

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
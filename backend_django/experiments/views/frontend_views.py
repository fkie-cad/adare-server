from rest_framework import views
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import rest_framework.generics as generics
import rest_framework.status as http_status_codes

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from permissions import HasGroupPermission

from experiments.models import Experiment, ExperimentRun, Scenario

from experiments.serializers.frontend_serializers import ExperimentRunSerializer, ScenarioSerializer, ExperimentSerializer


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
    # only for retrieve
    lookup_field = 'uuid'


class ExperimentRunCreateView(generics.CreateAPIView):
    serializer_class = ExperimentRun
    queryset = ExperimentRun.objects.all()
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': ['supervisor'],
    }
    # only for retrieve
    lookup_field = 'uuid'


class ScenarioRetrieveView(generics.RetrieveAPIView):
    serializer_class = ScenarioSerializer
    queryset = Scenario.objects.all()
    permission_classes = [AllowAny]
    # only for retrieve
    lookup_field = 'uuid'

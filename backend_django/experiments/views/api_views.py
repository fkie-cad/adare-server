from rest_framework import views, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from experiments.database_api.requests import create_request_experiment_creation, accept_request_experiment_creation

from permissions import HasGroupPermission


class ExperimentRequestView(generics.CreateAPIView):
    """
        Request the creation of a new scenario
    """
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):

        msg, status_code = create_request_experiment_creation(data_dict=request.data, requestor=request.user)
        return Response(data=msg, status=status_code)


class ExperimentRequestAcceptView(generics.CreateAPIView):
    """
        Accept the creation of a new scenario
    """
    permission_classes = (IsAuthenticated, HasGroupPermission)
    required_groups = {
        'POST': ['supervisor'],
    }

    def create(self, request, *args, **kwargs):
        msg, status_code = accept_request_experiment_creation(data_dict=request.data, supervisor=request.user)
        return Response(data=msg, status=status_code)


class ScenarioRequestView(generics.CreateAPIView):
    """
        Request the creation of a new experiment
    """
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        pass

"""
Bundle views - Returns a JSON manifest with experiment + all dependencies
so the client can download everything in one request.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from experiments.models import Experiment
from experiments.serializers import ExperimentSerializer, EnvironmentSerializer, TestFunctionSetSerializer
from helperfunctions.gitea import convert_gitea_internal_api_url_to_external

import logging

log = logging.getLogger(__name__)


class ExperimentBundleView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, ulid):
        experiment = Experiment.objects.filter(ulid=ulid).first()
        if not experiment:
            return Response({'error': 'Experiment not found'}, status=404)

        # Collect all environments
        environments = []
        for env in experiment.environments.all():
            env_data = EnvironmentSerializer(env).data
            environments.append(env_data)

        # Collect all testfunction sets referenced by abstract tests
        testfunction_set_ids = set()
        for at in experiment.abstract_tests.all():
            testfunction_set_ids.add(at.testfunction.testfunction_set_id)

        testfunction_sets = []
        from experiments.models import TestfunctionSet
        for tfset_id in testfunction_set_ids:
            tfset = TestfunctionSet.objects.filter(ulid=tfset_id).first()
            if tfset:
                tfset_data = TestFunctionSetSerializer(tfset).data
                testfunction_sets.append(tfset_data)

        experiment_data = ExperimentSerializer(experiment).data

        bundle = {
            'experiment': experiment_data,
            'environments': environments,
            'testfunction_sets': testfunction_sets,
        }

        return Response(bundle)

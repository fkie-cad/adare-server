"""
Dev-mode submit views — skip Gitea and return fake PR responses.

Only active when MODE=development (guarded at the URL layer in urls.py).
"""
import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser


VALID_ACTIONS = ('create', 'modify', 'remove')


def _fake_pr():
    return Response({'pr_url': '#dev', 'pr_number': random.randint(1000, 9999)}, status=201)


class DevSubmitExperimentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        name = request.data.get('name')
        action = request.data.get('action', 'create')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if action not in VALID_ACTIONS:
            return Response({'error': f'action must be one of {VALID_ACTIONS}'}, status=400)
        if action == 'create' and (not request.FILES.get('playbook') or not request.FILES.get('metadata')):
            return Response({'error': 'playbook and metadata are required'}, status=400)

        return _fake_pr()


class DevSubmitTestfunctionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        name = request.data.get('name')
        action = request.data.get('action', 'create')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if action not in VALID_ACTIONS:
            return Response({'error': f'action must be one of {VALID_ACTIONS}'}, status=400)
        if action == 'create' and (not request.FILES.get('testfunction') or not request.FILES.get('requirements')):
            return Response({'error': 'testfunction and requirements are required'}, status=400)

        return _fake_pr()


class DevSubmitEnvironmentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        name = request.data.get('name')
        action = request.data.get('action', 'create')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if action not in VALID_ACTIONS:
            return Response({'error': f'action must be one of {VALID_ACTIONS}'}, status=400)
        if action != 'remove' and not request.FILES.get('environment'):
            return Response({'error': 'environment is required'}, status=400)

        return _fake_pr()

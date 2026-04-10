"""
Dev-mode submit views — skip Gitea and return fake PR responses.

Only active when MODE=development (guarded at the URL layer in urls.py).
"""
import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser


class DevSubmitExperimentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        playbook = request.FILES.get('playbook')
        metadata = request.FILES.get('metadata')
        name = request.data.get('name')
        description = request.data.get('description', '')  # noqa: F841

        if not playbook or not metadata or not name:
            return Response({'error': 'playbook, metadata, and name are required'}, status=400)

        return Response({
            'pr_url': '#dev',
            'pr_number': random.randint(1000, 9999),
        }, status=201)


class DevSubmitTestfunctionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        testfunction_file = request.FILES.get('testfunction')
        requirements_file = request.FILES.get('requirements')
        name = request.data.get('name')
        description = request.data.get('description', '')  # noqa: F841

        if not testfunction_file or not requirements_file or not name:
            return Response({'error': 'testfunction, requirements, and name are required'}, status=400)

        return Response({
            'pr_url': '#dev',
            'pr_number': random.randint(1000, 9999),
        }, status=201)


class DevSubmitEnvironmentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        environment_file = request.FILES.get('environment')
        name = request.data.get('name')
        description = request.data.get('description', '')  # noqa: F841

        if not environment_file or not name:
            return Response({'error': 'environment and name are required'}, status=400)

        return Response({
            'pr_url': '#dev',
            'pr_number': random.randint(1000, 9999),
        }, status=201)

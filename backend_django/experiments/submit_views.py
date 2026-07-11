"""
Submit views - Proxy endpoints for creating Gitea PRs from the frontend.

These views receive uploaded files and create branches/PRs in the shared
Gitea repository using the server's credentials.
"""
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from django.conf import settings

from helperfunctions.gitea_write import create_branch, upload_file, create_pull_request
from giteaeventmanager.service import ingest_pr
from giteaeventmanager.exception import TaskFailure

import requests as req_lib
import logging

log = logging.getLogger(__name__)


def _submit_and_ingest(entity_type: str, name: str, files: dict, username: str, description: str):
    """Open the PR, then run the same synchronous ingest the pipeline runs.

    Ingesting in-process (not over HTTP) gives the submitter instant pass/fail
    and is idempotent, so the pipeline re-running ingest on the same PR is a no-op.

    Returns ``(response_body, status_code)``.
    """
    pr = _submit_files(
        entity_type=entity_type,
        name=name,
        files=files,
        username=username,
        description=description,
    )
    body = {'pr_url': pr['html_url'], 'pr_number': pr['number']}
    try:
        body['ingest'] = ingest_pr(pr['number'])
    except TaskFailure as e:
        # the PR exists but ingestion failed — tell the submitter immediately
        log.warning(f'inline ingest failed for {entity_type} pr {pr["number"]}: {e}')
        body['error'] = str(e)
        return body, 400
    return body, 201


class SubmitExperimentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        playbook = request.FILES.get('playbook')
        metadata = request.FILES.get('metadata')
        name = request.data.get('name')
        description = request.data.get('description', '')

        if not playbook or not metadata or not name:
            return Response({'error': 'playbook, metadata, and name are required'}, status=400)

        try:
            body, status = _submit_and_ingest(
                entity_type='experiment',
                name=name,
                files={
                    f'experiments/{name}/playbook.yml': playbook.read(),
                    f'experiments/{name}/metadata.yml': metadata.read(),
                },
                username=request.user.username,
                description=description,
            )
            return Response(body, status=status)
        except (RuntimeError, req_lib.HTTPError, req_lib.ConnectionError) as e:
            log.error(f'Failed to submit experiment: {e}')
            return Response({'error': str(e)}, status=500)


class SubmitTestfunctionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        testfunction_file = request.FILES.get('testfunction')
        requirements_file = request.FILES.get('requirements')
        name = request.data.get('name')
        description = request.data.get('description', '')

        if not testfunction_file or not requirements_file or not name:
            return Response({'error': 'testfunction, requirements, and name are required'}, status=400)

        try:
            body, status = _submit_and_ingest(
                entity_type='testfunction',
                name=name,
                files={
                    f'testfunctions/{name}/{name}.py': testfunction_file.read(),
                    f'testfunctions/{name}/requirements.txt': requirements_file.read(),
                },
                username=request.user.username,
                description=description,
            )
            return Response(body, status=status)
        except (RuntimeError, req_lib.HTTPError, req_lib.ConnectionError) as e:
            log.error(f'Failed to submit testfunction: {e}')
            return Response({'error': str(e)}, status=500)


class SubmitEnvironmentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        environment_file = request.FILES.get('environment')
        name = request.data.get('name')
        description = request.data.get('description', '')

        if not environment_file or not name:
            return Response({'error': 'environment and name are required'}, status=400)

        try:
            body, status = _submit_and_ingest(
                entity_type='environment',
                name=name,
                files={
                    f'environments/{name}.yml': environment_file.read(),
                },
                username=request.user.username,
                description=description,
            )
            return Response(body, status=status)
        except (RuntimeError, req_lib.HTTPError, req_lib.ConnectionError) as e:
            log.error(f'Failed to submit environment: {e}')
            return Response({'error': str(e)}, status=500)


def _submit_files(entity_type: str, name: str, files: dict[str, bytes], username: str, description: str = '') -> dict:
    """Create a branch, upload files, and open a PR."""
    owner = settings.GITEA_EXPERIMENTS_REPO_OWNER
    repo = settings.GITEA_EXPERIMENTS_REPO

    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    branch_name = f'submit/{entity_type}/{name}-{timestamp}'

    if not create_branch(owner, repo, branch_name):
        raise RuntimeError(f'Failed to create branch {branch_name}')

    for filepath, content in files.items():
        if not upload_file(owner, repo, filepath, content, branch_name,
                           message=f'[{entity_type} create] Add {filepath}'):
            raise RuntimeError(f'Failed to upload {filepath}')

    file_list = '\n'.join(f'- {fp}' for fp in files)
    body = f"""## Description
{description or '_No description provided._'}

## Submitted By
@{username} via ADARE Web

## Entity
- Type: {entity_type}
- Name: {name}
- Action: create

## Files
{file_list}"""

    pr = create_pull_request(
        owner, repo,
        title=f'[{entity_type} create] {name}',
        head=branch_name,
        body=body,
    )
    return pr

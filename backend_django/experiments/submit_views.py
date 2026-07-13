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

from helperfunctions.gitea_write import (
    create_branch, upload_file, delete_file, create_pull_request, find_open_pull_request,
)
from giteaeventmanager.service import ingest_pr, classify_submission
from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.errorcodes import SubmitErrorCode

import requests as req_lib
import logging

log = logging.getLogger(__name__)

VALID_ACTIONS = ('create', 'modify', 'remove')


class SubmitPrecheckView(APIView):
    """Name-based pre-submit classification for the interactive surfaces.

    Lets the CLI/React warn *before* opening a create PR (already-published ->
    guide to modify; open-duplicate -> point at the existing PR), avoiding the
    create-then-auto-close churn the async path performs. Read-only: no Gitea
    write, no file download. Registered mode-independently (dev and prod).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        entity_type = request.data.get('entity_type') or request.data.get('type')
        name = request.data.get('name')
        if not entity_type or not name:
            return Response({'error': 'entity_type and name are required'}, status=400)
        try:
            result = classify_submission(entity_type, name)
        except TaskFailure as e:
            return Response({'error': str(e), 'code': e.code}, status=400)
        return Response(result, status=200)


def _submit_and_ingest(entity_type: str, name: str, files: dict, username: str, description: str,
                       action: str = 'create', deletions: list[str] = None):
    """Open the PR, then run the same synchronous ingest the pipeline runs.

    Ingesting in-process (not over HTTP) gives the submitter instant pass/fail
    and is idempotent, so the pipeline re-running ingest on the same PR is a no-op.

    Returns ``(response_body, status_code)``.
    """
    # Pre-check a create *before* opening a PR: a terminal duplicate (already
    # published / open duplicate) should be guided, not turned into a PR the
    # async path would immediately auto-close.
    if action == 'create':
        classification = classify_submission(entity_type, name)
        code = classification.get('code')
        if code in (SubmitErrorCode.ALREADY_PUBLISHED, SubmitErrorCode.OPEN_DUPLICATE):
            body = {'error': classification['message'], 'code': code}
            if classification.get('pr_number') is not None:
                body['pr_number'] = classification['pr_number']
            return body, 409

    pr = _submit_files(
        entity_type=entity_type,
        name=name,
        files=files,
        username=username,
        description=description,
        action=action,
        deletions=deletions,
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
        name = request.data.get('name')
        description = request.data.get('description', '')
        action = request.data.get('action', 'create')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if action not in VALID_ACTIONS:
            return Response({'error': f'action must be one of {VALID_ACTIONS}'}, status=400)

        if action == 'remove':
            files = {}
            deletions = [f'experiments/{name}/playbook.yml', f'experiments/{name}/metadata.yml']
        else:
            playbook = request.FILES.get('playbook')
            metadata = request.FILES.get('metadata')
            files = {}
            if playbook:
                files[f'experiments/{name}/playbook.yml'] = playbook.read()
            if metadata:
                files[f'experiments/{name}/metadata.yml'] = metadata.read()
            # create needs the full pair; modify only needs the changed file(s)
            # (the PR branch is cut from main, so unchanged files carry over)
            if action == 'create' and len(files) < 2:
                return Response({'error': 'playbook and metadata are required'}, status=400)
            if action == 'modify' and not files:
                return Response({'error': 'at least one changed file is required to modify'}, status=400)
            deletions = None

        try:
            body, status = _submit_and_ingest(
                entity_type='experiment',
                name=name,
                files=files,
                username=request.user.username,
                description=description,
                action=action,
                deletions=deletions,
            )
            return Response(body, status=status)
        except (RuntimeError, req_lib.HTTPError, req_lib.ConnectionError) as e:
            log.error(f'Failed to submit experiment: {e}')
            return Response({'error': str(e)}, status=500)


class SubmitTestfunctionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        action = request.data.get('action', 'create')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if action not in VALID_ACTIONS:
            return Response({'error': f'action must be one of {VALID_ACTIONS}'}, status=400)

        if action == 'remove':
            files = {}
            deletions = [f'testfunctions/{name}/{name}.py', f'testfunctions/{name}/requirements.txt']
        else:
            testfunction_file = request.FILES.get('testfunction')
            requirements_file = request.FILES.get('requirements')
            files = {}
            if testfunction_file:
                files[f'testfunctions/{name}/{name}.py'] = testfunction_file.read()
            if requirements_file:
                files[f'testfunctions/{name}/requirements.txt'] = requirements_file.read()
            # create needs both files; modify only the changed file(s) (branch is cut from main)
            if action == 'create' and len(files) < 2:
                return Response({'error': 'testfunction and requirements are required'}, status=400)
            if action == 'modify' and not files:
                return Response({'error': 'at least one changed file is required to modify'}, status=400)
            deletions = None

        try:
            body, status = _submit_and_ingest(
                entity_type='testfunction',
                name=name,
                files=files,
                username=request.user.username,
                description=description,
                action=action,
                deletions=deletions,
            )
            return Response(body, status=status)
        except (RuntimeError, req_lib.HTTPError, req_lib.ConnectionError) as e:
            log.error(f'Failed to submit testfunction: {e}')
            return Response({'error': str(e)}, status=500)


class SubmitEnvironmentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        action = request.data.get('action', 'create')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if action not in VALID_ACTIONS:
            return Response({'error': f'action must be one of {VALID_ACTIONS}'}, status=400)

        if action == 'remove':
            files = {}
            deletions = [f'environments/{name}.yml']
        else:
            environment_file = request.FILES.get('environment')
            if not environment_file:
                return Response({'error': 'environment is required'}, status=400)
            files = {f'environments/{name}.yml': environment_file.read()}
            deletions = None

        try:
            body, status = _submit_and_ingest(
                entity_type='environment',
                name=name,
                files=files,
                username=request.user.username,
                description=description,
                action=action,
                deletions=deletions,
            )
            return Response(body, status=status)
        except (RuntimeError, req_lib.HTTPError, req_lib.ConnectionError) as e:
            log.error(f'Failed to submit environment: {e}')
            return Response({'error': str(e)}, status=500)


def _submit_files(entity_type: str, name: str, files: dict[str, bytes], username: str, description: str = '',
                  action: str = 'create', deletions: list[str] = None) -> dict:
    """Create a branch, upload/delete files, and open a PR.

    ``action`` is one of create/modify/remove and drives the commit messages, PR
    title, and body. ``files`` are uploaded (create/modify); ``deletions`` are
    repo paths removed on the branch (remove).
    """
    owner = settings.GITEA_EXPERIMENTS_REPO_OWNER
    repo = settings.GITEA_EXPERIMENTS_REPO
    deletions = deletions or []

    title = f'[{entity_type} {action}] {name}'
    head_prefix = f'submit/{entity_type}/{name}-'

    # Reuse an already-open create PR for this entity instead of opening a
    # duplicate (parity with the adare CLI): re-uploading pushes to the same
    # branch/PR, so the server ingests against the same gitea_pr_number and
    # idempotently upserts its draft (no name clash, no create-then-close churn).
    existing_pr = None
    if action == 'create':
        existing_pr = find_open_pull_request(owner, repo, title=title, head_prefix=head_prefix)

    if existing_pr:
        branch_name = existing_pr['head']['ref']
        log.info(f'Reusing open PR #{existing_pr["number"]} on branch {branch_name}')
    else:
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        branch_name = f'submit/{entity_type}/{name}-{timestamp}'
        if not create_branch(owner, repo, branch_name):
            raise RuntimeError(f'Failed to create branch {branch_name}')

    for filepath, content in files.items():
        if not upload_file(owner, repo, filepath, content, branch_name,
                           message=f'[{entity_type} {action}] Update {filepath}'):
            raise RuntimeError(f'Failed to upload {filepath}')

    for filepath in deletions:
        if not delete_file(owner, repo, filepath, branch_name,
                           message=f'[{entity_type} {action}] Delete {filepath}'):
            raise RuntimeError(f'Failed to delete {filepath}')

    changed = list(files) + deletions
    file_list = '\n'.join(f'- {fp}' for fp in changed)
    body = f"""## Description
{description or '_No description provided._'}

## Submitted By
@{username} via ADARE Web

## Entity
- Type: {entity_type}
- Name: {name}
- Action: {action}

## Files
{file_list}"""

    # Files were pushed to the reused PR's branch; no new PR to open.
    if existing_pr:
        return existing_pr

    pr = create_pull_request(
        owner, repo,
        title=title,
        head=branch_name,
        body=body,
    )
    return pr

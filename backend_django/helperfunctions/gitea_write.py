"""
Gitea API write operations for creating branches, uploading files, and creating PRs.

Uses the server's GITEA_API_USER/GITEA_API_PASSWORD credentials.
"""
import base64
import requests
from django.conf import settings
from giteaeventmanager.auth import GiteaAuthHandle

import logging

log = logging.getLogger(__name__)

WRITE_SCOPES = [
    "read:repository",
    "write:repository",
    "read:user",
]


def _get_token():
    return GiteaAuthHandle.get_token(scopes=WRITE_SCOPES)


def create_branch(repo_owner: str, repo_name: str, branch_name: str,
                   from_branch: str = 'main') -> bool:
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/branches'
    data = {
        'new_branch_name': branch_name,
        'old_branch_name': from_branch,
    }
    response = requests.post(url, json=data, headers={'Authorization': f'token {token}'})
    if response.status_code == 201:
        log.info(f'Created branch {branch_name}')
        return True
    log.error(f'Failed to create branch: {response.status_code} {response.text}')
    return False


def upload_file(repo_owner: str, repo_name: str, filepath: str,
                content: bytes, branch: str, message: str) -> bool:
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/contents/{filepath}'
    headers = {'Authorization': f'token {token}'}
    content_b64 = base64.b64encode(content).decode('ascii')

    # Check if file exists (need SHA for update)
    response = requests.get(url, params={'ref': branch}, headers=headers)
    data = {
        'message': message,
        'content': content_b64,
        'branch': branch,
    }
    if response.status_code == 200:
        existing = response.json()
        data['sha'] = existing['sha']

    response = requests.put(url, json=data, headers=headers)
    if response.status_code in (200, 201):
        log.info(f'Uploaded {filepath} to {branch}')
        return True
    log.error(f'Failed to upload {filepath}: {response.status_code} {response.text}')
    return False


def delete_file(repo_owner: str, repo_name: str, filepath: str,
                branch: str, message: str) -> bool:
    """Delete a file on ``branch`` (used by remove PRs). Idempotent: an
    already-absent file is treated as success."""
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/contents/{filepath}'
    headers = {'Authorization': f'token {token}'}

    # Gitea requires the current blob SHA to delete a file.
    response = requests.get(url, params={'ref': branch}, headers=headers)
    if response.status_code == 404:
        log.info(f'{filepath} already absent on {branch}, nothing to delete')
        return True
    if response.status_code != 200:
        log.error(f'Failed to read {filepath} for delete: {response.status_code} {response.text}')
        return False

    data = {
        'message': message,
        'sha': response.json()['sha'],
        'branch': branch,
    }
    response = requests.delete(url, json=data, headers=headers)
    if response.status_code == 200:
        log.info(f'Deleted {filepath} from {branch}')
        return True
    log.error(f'Failed to delete {filepath}: {response.status_code} {response.text}')
    return False


def create_pull_request(repo_owner: str, repo_name: str, title: str,
                         head: str, base: str = 'main', body: str = '') -> dict:
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/pulls'
    data = {
        'title': title,
        'head': head,
        'base': base,
        'body': body,
    }
    response = requests.post(url, json=data, headers={'Authorization': f'token {token}'})
    response.raise_for_status()
    pr = response.json()
    log.info(f'Created PR #{pr["number"]}: {title}')
    return pr


def find_open_pull_request(repo_owner: str, repo_name: str,
                           title: str = None, head_prefix: str = None) -> dict | None:
    """Return the first open PR matching by exact title or head-branch prefix.

    Port of the adare client's ``GiteaApiClient.find_open_pull_request`` so the
    React proxy reuses an already-open submit PR instead of opening a duplicate
    (the submit branch carries a timestamp suffix, so we match on the stable
    title or the ``submit/<entity>/<name>-`` head prefix). Returns ``None`` if
    none match.
    """
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/pulls'
    response = requests.get(url, params={'state': 'open', 'limit': 50},
                            headers={'Authorization': f'token {token}'})
    response.raise_for_status()
    for pr in response.json():
        if title is not None and pr.get('title') == title:
            return pr
        head_ref = (pr.get('head') or {}).get('ref', '')
        if head_prefix is not None and head_ref.startswith(head_prefix):
            return pr
    return None


def comment_on_pull_request(repo_owner: str, repo_name: str, number: int, body: str) -> bool:
    """Add a comment to a pull request (Gitea treats PRs as issues for comments).

    Used to explain an automatic close of a terminal-duplicate PR. Returns True
    on success; logs and returns False on a non-2xx response.
    """
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/issues/{number}/comments'
    response = requests.post(url, json={'body': body}, headers={'Authorization': f'token {token}'})
    if response.status_code in (200, 201):
        log.info(f'Commented on PR #{number}')
        return True
    log.error(f'Failed to comment on PR #{number}: {response.status_code} {response.text}')
    return False


def close_pull_request(repo_owner: str, repo_name: str, number: int) -> bool:
    """Close a pull request (``state: closed``) without merging.

    Used to auto-close terminal-duplicate submit PRs. Returns True on success;
    logs and returns False on a non-2xx response.
    """
    token = _get_token()
    url = f'{settings.GITEA_API}repos/{repo_owner}/{repo_name}/pulls/{number}'
    response = requests.patch(url, json={'state': 'closed'}, headers={'Authorization': f'token {token}'})
    if response.status_code == 200:
        log.info(f'Closed PR #{number}')
        return True
    log.error(f'Failed to close PR #{number}: {response.status_code} {response.text}')
    return False

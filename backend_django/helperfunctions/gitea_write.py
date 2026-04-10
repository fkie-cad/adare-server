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

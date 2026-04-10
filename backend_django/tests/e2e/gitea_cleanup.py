"""
Gitea test helper for E2E tests.

Manages Gitea repo state: creating branches, uploading files, creating/merging PRs,
and cleaning up after tests. Refactored from tests/gitea_tests/pr.py to accept
configuration from Django settings instead of module-level globals.
"""
import base64
import json
import time
from pathlib import Path

import giteaapi as gitea


class GiteaTestHelper:
    """Manages Gitea repo state for E2E tests."""

    def __init__(self, api_url, api_user, api_password, owner, repo):
        conf = gitea.Configuration()
        conf.host = api_url
        conf.username = api_user
        conf.password = api_password
        self.api = gitea.ApiClient(conf)
        self.repo_api = gitea.RepositoryApi(self.api)
        self.owner = owner
        self.repo = repo

    def full_reset(self):
        """Close PRs, delete branches, clear files."""
        self.close_all_prs()
        self.delete_all_branches_except_main()
        self.clear_branch('main')

    def close_all_prs(self):
        prs = self.repo_api.repo_list_pull_requests(owner=self.owner, repo=self.repo)
        for pr in prs:
            if pr.state == 'open':
                self.repo_api.repo_edit_pull_request(
                    owner=self.owner, repo=self.repo, index=pr.number,
                    body={"state": "closed"},
                )

    def delete_all_branches_except_main(self):
        branches = self.repo_api.repo_list_branches(owner=self.owner, repo=self.repo)
        for branch in branches:
            if branch.name != 'main':
                self.repo_api.repo_delete_branch(
                    owner=self.owner, repo=self.repo, branch=branch.name,
                )

    def clear_branch(self, branch='main'):
        self._delete_files_recursive(branch, '')

    def _delete_files_recursive(self, branch, path, exclude=None):
        if exclude is None:
            exclude = ['.gitignore', 'README.md', '.gitea']
        if path == '':
            files = self.repo_api.repo_get_contents_list(
                owner=self.owner, repo=self.repo, ref=branch,
            )
        else:
            files = self.repo_api.repo_get_contents(
                owner=self.owner, repo=self.repo, filepath=path, ref=branch,
            )
        for file in files:
            if file.name in exclude:
                continue
            if file.type == 'file':
                self.repo_api.repo_delete_file(
                    owner=self.owner, repo=self.repo, filepath=file.path,
                    body={"branch": branch, "message": "clear branch", "sha": file.sha},
                )
            elif file.type == 'dir':
                self._delete_files_recursive(branch, file.path, exclude)

    def create_branch(self, new_branch_name, old_branch='main'):
        return self.repo_api.repo_create_branch(
            owner=self.owner, repo=self.repo,
            body={"base": old_branch, "new_branch_name": new_branch_name},
        )

    def upload_file(self, branch, local_file, git_path, commit_msg=None):
        with open(local_file, "rb") as f:
            content = f.read()
        base64_content = base64.b64encode(content).decode("utf-8")
        if not commit_msg:
            commit_msg = f"upload {git_path}"
        self.repo_api.repo_create_file(
            owner=self.owner, repo=self.repo, filepath=git_path,
            body={"content": base64_content, "branch": branch, "message": commit_msg},
        )

    def create_pr(self, title, head_branch, base_branch='main', body=''):
        pr = self.repo_api.repo_create_pull_request(
            owner=self.owner, repo=self.repo,
            body={"title": title, "body": body or title, "head": head_branch, "base": base_branch},
        )
        return pr

    def merge_pr(self, pr_number, retries=3, delay=3):
        """Merge a PR, retrying if Gitea isn't ready yet."""
        for attempt in range(retries):
            try:
                return self.repo_api.repo_merge_pull_request(
                    owner=self.owner, repo=self.repo, index=pr_number,
                    body={"do": "merge"},
                )
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise

    def create_pr_testfunction(self, name, files_dir):
        """Create a PR for a new testfunction set."""
        branch_name = f'testfunction/{name}'
        self.create_branch(branch_name)
        files_dir = Path(files_dir)
        for file in files_dir.rglob("*"):
            if file.is_file():
                git_path = f'testfunctions/{name}/{file.relative_to(files_dir)}'
                self.upload_file(branch_name, file, git_path)
        title = f'[testfunction create] {name}'
        pr = self.create_pr(title, branch_name)
        return pr

    def create_pr_environment(self, name, file_path):
        """Create a PR for a new environment."""
        branch_name = f'environment/{name}'
        self.create_branch(branch_name)
        file_path = Path(file_path)
        git_path = f'environments/{name}.yml'
        self.upload_file(branch_name, file_path, git_path)
        title = f'[environment create] {name}'
        pr = self.create_pr(title, branch_name)
        return pr

    def create_pr_experiment(self, name, files_dir):
        """Create a PR for a new experiment."""
        branch_name = f'experiment/{name}'
        self.create_branch(branch_name)
        files_dir = Path(files_dir)
        for file in files_dir.rglob("*"):
            if file.is_file():
                git_path = f'experiments/{name}/{file.relative_to(files_dir)}'
                self.upload_file(branch_name, file, git_path)
        time.sleep(1)  # Brief pause to let Gitea index files
        title = f'[experiment create] {name}'
        pr = self.create_pr(title, branch_name)
        return pr

    def build_webhook_payload(self, pr, action='opened'):
        """Build a Gitea webhook payload from a PR object."""
        merged = action == 'closed' and hasattr(pr, 'merged') and pr.merged
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        def _to_iso(dt):
            if dt is None:
                return now_iso
            if isinstance(dt, str):
                return dt
            return dt.strftime("%Y-%m-%dT%H:%M:%S%z")

        pr_url = f"https://gitea/{self.owner}/{self.repo}/pulls/{pr.number}"
        payload = {
            "action": action,
            "number": pr.number,
            "pull_request": {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body or "",
                "state": pr.state,
                "merged": merged,
                "merged_at": _to_iso(getattr(pr, 'merged_at', None)) if merged else None,
                "url": getattr(pr, 'url', None) or pr_url,
                "html_url": getattr(pr, 'html_url', None) or pr_url,
                "created_at": _to_iso(getattr(pr, 'created_at', None)),
                "updated_at": _to_iso(getattr(pr, 'updated_at', None)),
                "user": {
                    "id": pr.user.id if pr.user else 0,
                    "login": pr.user.login if pr.user else "",
                    "email": pr.user.email if pr.user else "",
                },
                "head": {
                    "ref": pr.head.ref if pr.head else "",
                    "sha": pr.head.sha if pr.head else "",
                },
                "base": {
                    "ref": pr.base.ref if pr.base else "main",
                },
                "labels": [
                    {"id": l.id, "name": l.name, "color": l.color, "description": getattr(l, 'description', '')}
                    for l in (pr.labels or [])
                ],
                "assignee": None,
                "assignees": [
                    {"id": a.id, "login": a.login}
                    for a in (pr.assignees or [])
                ],
                "requested_reviewers": [],
            },
            "repository": {
                "name": self.repo,
                "full_name": f"{self.owner}/{self.repo}",
                "owner": {
                    "login": self.owner,
                },
            },
            "sender": {
                "id": pr.user.id if pr.user else 0,
                "login": pr.user.login if pr.user else "",
            },
        }
        if merged:
            payload["pull_request"]["merged_by"] = payload["pull_request"]["user"]
        return payload

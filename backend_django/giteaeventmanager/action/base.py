from users.models import GiteaUser
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from experiments.models import Request
from django.db import transaction
from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.errorcodes import SubmitErrorCode
from helperfunctions.hash import hash_file_sha256
from giteaeventmanager.action.plugin import PullRequestPlugin
from giteaeventmanager.auth import GiteaAuthHandle
from django.conf import settings
import requests

import logging
log = logging.getLogger(__name__)


def find_owning_request(obj) -> Request:
    """Find the Request that owns ``obj`` via its generic foreign key (or None).

    Module-level so the pre-submit classifier (``service.classify_submission``)
    can reuse the exact same ownership rule as ``PRIngestCreate``.
    """
    from django.contrib.contenttypes.models import ContentType
    content_type = ContentType.objects.get_for_model(type(obj))
    return Request.objects.filter(objective=content_type, object_id=obj.pk).first()


class AbstractPullRequest(ABC):
    @abstractmethod
    def check(self) -> (bool, str):
        pass

    @abstractmethod
    def action(self) -> (bool, str):
        pass


class PullRequest(AbstractPullRequest):
    request: Request = None
    pullrequest_plugin: PullRequestPlugin = None

    title: str
    description: str
    last_commit: str = None
    data: dict
    objective: str
    action_type: str
    object_name: str
    tmp_dir: Path = None

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                 object_name: str):
        self.pullrequest_plugin = pullrequest_plugin

        self.title = json_data["pull_request"]["title"]
        # self.description = json_data["body"]
        self.description = ""
        self.objective = objective
        self.action_type = action
        self.object_name = object_name

        # get last commit
        self.last_commit = json_data["pull_request"]["head"]["sha"]

        self.data = json_data

        self.request = Request.objects.filter(gitea_pr_number=self.data["number"]).first()

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def action(self):
        pass

    def _request_exists(self):
        return Request.objects.filter(gitea_pr_number=self.data["number"]).exists()

    def _get_user(self, user_data: dict):
        username = user_data["login"]
        # due to a bug/feature (https://github.com/go-gitea/gitea/pull/27943) the email is set to a noreply using username as email
        # however we need the real email to create the user -> we therefore retrieve the email by accessing giteas users api
        token = GiteaAuthHandle.get_token()
        api_url = f'{settings.GITEA_API}users/{username}'
        headers = {'Authorization': f'token {token}'}
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise TaskFailure(f'could not retrieve user data for {username} ({response.status_code}): {response.text}',
                              code=SubmitErrorCode.UPSTREAM_UNAVAILABLE)
        fetched_user_data = response.json()

        gitea_user_id = fetched_user_data["id"]

        user = GiteaUser.objects.filter(gitea_id=gitea_user_id).first()
        if not user:
            user = GiteaUser(gitea_id=gitea_user_id, username=username, email=fetched_user_data["email"])
        else:
            user.email = fetched_user_data["email"]
            user.username = username

        user.avatar = fetched_user_data["avatar_url"]
        user.save()

        return user

    def _get_pr_users(self) -> (GiteaUser, list[GiteaUser], list[GiteaUser]):
        requester: GiteaUser = self._get_user(self.data["pull_request"]["user"])
        assignee_users: list[GiteaUser] = []
        reviewer_users: list[GiteaUser] = []
        if self.data["pull_request"]["assignee"]:
            assignee_users = [self._get_user(assignee) for assignee in self.data["pull_request"]["assignees"]]
        if self.data["pull_request"]["requested_reviewers"]:
            reviewer_users = [self._get_user(reviewer) for reviewer in self.data["pull_request"]["requested_reviewers"]]

        return requester, assignee_users, reviewer_users

    def _update_pr_users(self):
        requester, assignee_users, reviewer_users = self._get_pr_users()
        self.request.requester = requester
        self.request.assignees.set(assignee_users)
        self.request.reviewers.set(reviewer_users)
        self.request.save()

    def _get_pr_requester(self) -> GiteaUser:
        return self._get_user(self.data["pull_request"]["user"])

    def _get_pr_dates(self) -> (datetime, datetime):
        creation_date = datetime.strptime(self.data["pull_request"]["created_at"], "%Y-%m-%dT%H:%M:%S%z")
        last_change_date = datetime.strptime(self.data["pull_request"]["updated_at"], "%Y-%m-%dT%H:%M:%S%z")
        return creation_date, last_change_date

    @transaction.atomic
    def _update_labels(self):
        labels = self.data["pull_request"]["labels"]
        self.request.labels.clear()
        for label in labels:
            label_instance, _ = self.request.labels.get_or_create(gitea_label_id=label["id"], name=label["name"], color=label["color"], description=label["description"])
            self.request.labels.add(label_instance)

    def _create_pull_request(self, object_instance) -> Request:
        requester, assignee_users, reviewer_users = self._get_pr_users()
        creation_date, last_change_date = self._get_pr_dates()
        request = Request(
            title=self.title,
            description=self.description,
            gitea_pr_url=self.data["pull_request"]["url"],
            gitea_pr_status=self.data["pull_request"]["state"],
            gitea_pr_number=self.data["number"],
            object=object_instance,
            action=self.action_type,
            objective_name=self.objective,
            creation_date=creation_date,
            last_change_date=last_change_date,
            requester=requester
        )
        request.save()
        request.assignees.set(assignee_users)
        request.reviewers.set(reviewer_users)
        return request

    def _get_pull_request(self):
        return Request.objects.filter(gitea_pr_number=self.data["number"]).first()

    def _create_pull_request_modify(self, object_instance) -> Request:
        """Create a modify Request: ``object`` is the proposed new draft,
        ``old_object`` is the currently-published object it will replace on merge.

        Must be called *after* the new draft has been created; ``get_object()`` is
        published-aware, so it resolves to the live object (not the fresh draft).
        """
        old_object = self.pullrequest_plugin.get_object()
        request = self._create_pull_request(object_instance)
        request.old_object = old_object
        request.old_objective_name = self.objective
        request.save()
        return request

    def _download_and_hash(self, raise_error_on_missing_files: bool = True):
        downloaded_files, missing_files = self.pullrequest_plugin.download()
        if missing_files and raise_error_on_missing_files:
            self.pullrequest_plugin.cleanup()
            raise TaskFailure(f'missing files for pull request open ({[file.as_posix() for file in missing_files]})',
                              code=SubmitErrorCode.MISSING_FILES)
        self.pullrequest_plugin.check_file_validity()
        self.pullrequest_plugin.hash()
        return downloaded_files, missing_files

    def cleanup(self):
        self.pullrequest_plugin.cleanup()

    @staticmethod
    def _transform_gitea_date(date: str) -> datetime:
        return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")


class PRClosed(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                 object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self) -> (bool, str):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist',
                              code=SubmitErrorCode.NOT_FOUND)

    @transaction.atomic
    def __db_merge_pr(self):
        self.request.object.published = True
        self.request.object.published_at = self._transform_gitea_date(self.data["pull_request"]["merged_at"])
        self.request.object.published_by = self._get_user(self.data["pull_request"]["merged_by"])
        self.request.object.created_by = self._get_user(self.data["pull_request"]["user"])
        self.request.object.created_at = self._transform_gitea_date(self.data["pull_request"]["created_at"])
        self.request.object.save()

    @transaction.atomic
    def __db_delete_pr(self):
        self.request.delete()

    def action(self) -> (bool, str):
        merged = self.data["pull_request"]["merged"]
        if merged:
            self.__db_merge_pr()
        self.__db_delete_pr()


class PROpenedCreate(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                 object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} already exists',
                              code=SubmitErrorCode.INVALID_STATE)

        self._download_and_hash()

        # check if object does already exist
        object_instance = self.pullrequest_plugin.get_object()
        if object_instance:
            raise TaskFailure(f'{self.object_name} already exists', code=SubmitErrorCode.ALREADY_PUBLISHED)

        # check if object with same content/hash already exists
        existing_object = self.pullrequest_plugin.get_object_by_hash()
        if existing_object:
            raise TaskFailure(f'{self.object_name} with same content already exists',
                              code=SubmitErrorCode.CONTENT_DUPLICATE)

    @transaction.atomic
    def action(self):
        object_instance = self.pullrequest_plugin.update_object(self._get_pr_requester())
        self.request = self._create_pull_request(object_instance)
        self.cleanup()


class PRIngestCreate(PullRequest):
    """Idempotent create used by the synchronous ingest endpoint.

    Reached by two triggers (client inline submit, Actions pipeline) and safe to
    re-run for the same PR. Keyed by ``Request.gitea_pr_number``:

    * no request for this PR -> create the draft object (``published=False``) + request
    * request already exists (re-run / synchronize) -> replace the draft from the new content
    """

    # draft (name collision) scheduled for reconciliation in action(); set in check()
    _stale_object = None
    _stale_request: Request = None

    def _find_owning_request(self, obj) -> Request:
        """Find the Request that owns ``obj`` via its generic foreign key (or None)."""
        return find_owning_request(obj)

    def _auto_close_terminal_duplicate(self, comment: str):
        """Comment on and close the PR being ingested (``self.data['number']``).

        Called for terminal wrong-ops (already-published / open-duplicate) so a
        stray duplicate PR that still reaches ingest is cleaned up on the async
        path instead of lingering open. Uses the server's ``write:repository``
        token (the same one that authors submit PRs). Never closes the *other*
        owning PR (#M) — only the newer, colliding one.

        Best-effort: guarded by ``AUTO_CLOSE_TERMINAL_DUPLICATES`` and swallows
        Gitea transport errors so a close failure still yields the clean coded
        400 rather than a 500. No loop risk: closing emits a ``closed`` event
        that routes to ``finalize`` (a no-op with no draft), not back to ingest.
        """
        if not getattr(settings, 'AUTO_CLOSE_TERMINAL_DUPLICATES', True):
            return
        from helperfunctions import gitea_write
        owner = settings.GITEA_EXPERIMENTS_REPO_OWNER
        repo = settings.GITEA_EXPERIMENTS_REPO
        number = self.data["number"]
        try:
            gitea_write.comment_on_pull_request(owner, repo, number, comment)
            gitea_write.close_pull_request(owner, repo, number)
        except requests.RequestException as e:
            log.error(f'auto-close of terminal-duplicate PR #{number} failed: {e}')

    def _resolve_name_collision(self, obj) -> Request:
        """An object with this name already exists. Decide what it means.

        * published object -> terminal wrong-op; auto-close this PR and reject
          (the caller should open a *modify* PR).
        * unpublished draft owned by a *still-open* PR -> genuine concurrent
          duplicate; auto-close this (newer) PR and reject, pointing at #M.
        * unpublished draft whose owning PR is closed/merged/absent -> a stale
          draft (finalize never ran); return the owning Request so ``action()``
          can reconcile it away and recreate under the new PR.

        Returns the stale ``Request`` to reconcile (may be ``None`` for an orphan
        draft with no owning request), or raises coded ``TaskFailure``.
        """
        if getattr(obj, 'published', False):
            self._auto_close_terminal_duplicate(
                f'`{self.object_name}` is already published, so this create pull request cannot '
                f'be ingested. Closing it automatically — open a **modify** pull request to '
                f'change the published version instead.')
            raise TaskFailure(
                f'{self.object_name} is already published — submit a modify PR, not a create.',
                code=SubmitErrorCode.ALREADY_PUBLISHED)

        owning_request = self._find_owning_request(obj)
        if owning_request is None:
            # orphan draft with no owning request -> stale, nothing to fetch
            return None

        other_pr = owning_request.gitea_pr_number
        from giteaeventmanager.service import _fetch_pull_request
        try:
            pr = _fetch_pull_request(other_pr)
        except TaskFailure:
            # owning PR is gone / unfetchable -> stale draft, reconcile it
            return owning_request

        if pr.get('state') == 'open' and not pr.get('merged'):
            self._auto_close_terminal_duplicate(
                f'`{self.object_name}` is already proposed by open pull request #{other_pr}. '
                f'Closing this duplicate automatically — please continue the work in #{other_pr}.')
            raise TaskFailure(
                f'{self.object_name} is already proposed by open pull request '
                f'#{other_pr}; update that PR instead of opening a new one.',
                code=SubmitErrorCode.OPEN_DUPLICATE)
        # closed / merged owning PR -> stale draft, reconcile it
        return owning_request

    def check(self):
        # always download + validate + hash so concrete errors surface as 4xx
        self._download_and_hash()

        if self._request_exists():
            # re-ingest of the same PR -> upsert, skip the duplicate guards below
            return

        # first ingest: an object with this name may already exist
        self._stale_object = None
        self._stale_request = None
        existing_by_name = self.pullrequest_plugin.get_object()
        if existing_by_name:
            # raises on published / open-dup; returns the stale Request to reconcile
            self._stale_request = self._resolve_name_collision(existing_by_name)
            self._stale_object = existing_by_name

        # same-content guard, ignoring the stale draft we are about to reconcile
        existing_by_hash = self.pullrequest_plugin.get_object_by_hash()
        if existing_by_hash and existing_by_hash != self._stale_object:
            raise TaskFailure(f'{self.object_name} with same content already exists',
                              code=SubmitErrorCode.CONTENT_DUPLICATE)

    @transaction.atomic
    def action(self):
        if self._request_exists():
            existing = self.request.object
            if existing and existing.sha256hash == self.pullrequest_plugin.sha256:
                # content unchanged -> keep the draft (stable ULID), no DB churn
                self.cleanup()
                return
            # content changed -> drop the previous draft and recreate from the new content
            old_object = self.request.object
            self.request.delete()
            if old_object:
                old_object.delete()
        else:
            # reconcile a stale draft from a dead PR (determined in check())
            if self._stale_request is not None:
                self._stale_request.delete()
            if self._stale_object is not None:
                self._stale_object.delete()

        object_instance = self.pullrequest_plugin.update_object(self._get_pr_requester())
        self.request = self._create_pull_request(object_instance)
        self.cleanup()


class PRFinalize(PullRequest):
    """Finalize a closed PR for the synchronous finalize endpoint.

    Merge-gated and dispatched by action:

    * create -> merge publishes the draft (the published object stays); close
      without merge deletes the draft. No draft for this PR -> no-op.
    * modify -> merge publishes the proposed draft and deletes the old
      (previously-published) object; close without merge deletes the draft and
      keeps the old object live.
    * remove -> merge deletes the (still-published) object; close without merge
      keeps it. Either way the request is dropped.
    """

    def check(self):
        # tolerant: a close without a prior ingest is a no-op, not an error
        pass

    def _publish(self, object_instance, pr):
        object_instance.published = True
        object_instance.published_at = self._transform_gitea_date(pr["merged_at"])
        object_instance.published_by = self._get_user(pr["merged_by"])
        object_instance.created_by = self._get_user(pr["user"])
        object_instance.created_at = self._transform_gitea_date(pr["created_at"])
        object_instance.save()

    @transaction.atomic
    def action(self) -> dict:
        if self.action_type == "modify":
            return self._finalize_modify()
        if self.action_type == "remove":
            return self._finalize_remove()
        return self._finalize_create()

    def _finalize_create(self) -> dict:
        pr = self.data["pull_request"]
        merged = bool(pr.get("merged", False))

        if not self._request_exists():
            return {"action": "create", "merged": merged, "published": False, "deleted": False, "had_draft": False}

        object_instance = self.request.object
        if merged:
            self._publish(object_instance, pr)
            self.request.delete()
            return {"action": "create", "merged": True, "published": True, "deleted": False, "had_draft": True}

        self.request.delete()
        if object_instance:
            object_instance.delete()
        return {"action": "create", "merged": False, "published": False, "deleted": True, "had_draft": True}

    def _finalize_modify(self) -> dict:
        pr = self.data["pull_request"]
        merged = bool(pr.get("merged", False))

        if not self._request_exists():
            return {"action": "modify", "merged": merged, "published": False, "deleted": False, "had_draft": False}

        new_draft = self.request.object
        old_object = self.request.old_object
        if merged:
            if new_draft:
                self._publish(new_draft, pr)
            # drop the request before removing the old object so no request points at it
            self.request.delete()
            if old_object:
                old_object.delete()
            return {"action": "modify", "merged": True, "published": True, "deleted_old": bool(old_object), "had_draft": True}

        # closed without merge -> discard the proposed draft, keep the old object live
        self.request.delete()
        if new_draft:
            new_draft.delete()
        return {"action": "modify", "merged": False, "published": False, "deleted": True, "had_draft": True}

    def _finalize_remove(self) -> dict:
        pr = self.data["pull_request"]
        merged = bool(pr.get("merged", False))

        if not self._request_exists():
            return {"action": "remove", "merged": merged, "deleted": False, "had_request": False}

        object_instance = self.request.object
        self.request.delete()
        if merged and object_instance:
            object_instance.delete()
            return {"action": "remove", "merged": True, "deleted": True, "had_request": True}
        return {"action": "remove", "merged": False, "deleted": False, "had_request": True}


class PRIngestModify(PullRequest):
    """Idempotent modify used by the synchronous ingest endpoint.

    Downloads + validates the proposed new files and records them as a draft
    (``published=False``) coexisting with the still-published object. The
    published object is stashed on ``Request.old_object`` and stays live until
    the PR merges. Safe to re-run for the same PR (upsert on ``gitea_pr_number``):

    * no request for this PR -> create the draft + modify request (old_object = live)
    * request already exists -> replace the draft from the new content, keep old_object
    """

    def check(self):
        # always download + validate + hash so concrete errors surface as 4xx
        self._download_and_hash()

        if self._request_exists():
            # re-ingest of the same PR -> upsert, skip the guards below
            return

        existing = self.pullrequest_plugin.get_object()
        if not existing:
            raise TaskFailure(f'{self.object_name} does not exist — submit a create PR, not a modify.',
                              code=SubmitErrorCode.NOT_FOUND)
        if not getattr(existing, 'published', False):
            raise TaskFailure(f'{self.object_name} is not published yet — cannot modify a draft.',
                              code=SubmitErrorCode.INVALID_STATE)

        # reject a no-op modify (new content identical to an existing object)
        existing_by_hash = self.pullrequest_plugin.get_object_by_hash()
        if existing_by_hash:
            raise TaskFailure(f'{self.object_name} with same content already exists — nothing to modify',
                              code=SubmitErrorCode.CONTENT_DUPLICATE)

    @transaction.atomic
    def action(self):
        if self._request_exists():
            existing_draft = self.request.object
            if existing_draft and existing_draft.sha256hash == self.pullrequest_plugin.sha256:
                # content unchanged -> keep the draft (stable ULID), no DB churn
                self.cleanup()
                return
            # content changed -> drop the previous draft and recreate; old_object is preserved
            if existing_draft:
                existing_draft.delete()
            new_draft = self.pullrequest_plugin.update_object(self._get_pr_requester())
            self.request.object = new_draft
            self.request.save()
            self.cleanup()
            return

        # first ingest: create the proposed draft, then record the modify request
        # (old_object = the currently-published object, resolved in _create_pull_request_modify)
        new_draft = self.pullrequest_plugin.update_object(self._get_pr_requester())
        self.request = self._create_pull_request_modify(new_draft)
        self.cleanup()


class PRIngestRemove(PullRequest):
    """Idempotent remove used by the synchronous ingest endpoint.

    The remove PR deletes the repo files on its branch; ingest verifies the
    object exists and is published and that its files are gone, then records a
    ``remove`` request pointing at the still-published object (no draft). The
    object is deleted only when the PR merges (in ``PRFinalize._finalize_remove``).
    Safe to re-run for the same PR.
    """

    def check(self):
        if self._request_exists():
            # re-ingest of the same PR -> request already recorded
            return

        object_instance = self.pullrequest_plugin.get_object()
        if not object_instance:
            raise TaskFailure(f'{self.object_name} does not exist', code=SubmitErrorCode.NOT_FOUND)
        if not getattr(object_instance, 'published', False):
            raise TaskFailure(f'{self.object_name} is not published yet — cannot remove a draft.',
                              code=SubmitErrorCode.INVALID_STATE)

        # the delete PR must actually remove the files on its branch
        downloaded_files, _ = self.pullrequest_plugin.download()
        self.pullrequest_plugin.cleanup()
        if downloaded_files:
            raise TaskFailure(
                f'remove request should delete all related files, but files are still present '
                f'on the pull request branch: {[file.as_posix() for file in downloaded_files]}',
                code=SubmitErrorCode.INVALID_CONTENT)

    @transaction.atomic
    def action(self):
        if self._request_exists():
            # idempotent: the remove request is already recorded
            self.cleanup()
            return
        object_instance = self.pullrequest_plugin.get_object()
        self.request = self._create_pull_request(object_instance)
        self.cleanup()


class PROpenedModify(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} already exists',
                              code=SubmitErrorCode.INVALID_STATE)

        self._download_and_hash()

        # check if (new) object does already exist
        object_instance = self.pullrequest_plugin.get_object()
        if object_instance:
            raise TaskFailure(f'{self.object_name} does not exist', code=SubmitErrorCode.NOT_FOUND)

        # check if object with same content/hash already exists
        existing_object = self.pullrequest_plugin.get_object_by_hash()
        if existing_object:
            raise TaskFailure(f'{self.object_name} with same content already exists - no change happened',
                              code=SubmitErrorCode.CONTENT_DUPLICATE)

    @transaction.atomic
    def action(self):
        object_instance = self.pullrequest_plugin.update_object(self._get_pr_requester())
        self.request = self._create_pull_request_modify(object_instance)
        self.cleanup()


class PROpenedDelete(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} already exists',
                              code=SubmitErrorCode.INVALID_STATE)

        object_instance = self.pullrequest_plugin.get_object()
        if not object_instance:
            raise TaskFailure(f'{self.object_name} does not exist', code=SubmitErrorCode.NOT_FOUND)

        downloaded_files, missing_files = self._download_and_hash(raise_error_on_missing_files=False)
        if downloaded_files:
            # if files are downloaded it means the request is erroneous
            self.cleanup()
            raise TaskFailure(f'delete request should delete all related files, but files are present: {[file.as_posix() for file in downloaded_files]}',
                              code=SubmitErrorCode.INVALID_CONTENT)

    @transaction.atomic
    def action(self):
        # create request
        object_instance = self.pullrequest_plugin.get_object()
        self.request = self._create_pull_request(object_instance)


class PRClosedModify(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                    object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        super().check()

    @transaction.atomic
    def action(self):
        self.request.old_object.delete()
        self.request.delete()


class PRClosedDelete(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                    object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        super().check()

    @transaction.atomic
    def action(self):
        self.request.object.delete()
        self.request.delete()


class PRAssigned(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist',
                              code=SubmitErrorCode.NOT_FOUND)

    @transaction.atomic
    def action(self):
        self._update_pr_users()


class PRUnassigned(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist',
                              code=SubmitErrorCode.NOT_FOUND)

    @transaction.atomic
    def action(self):
        self._update_pr_users()


class PRReviewRequested(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist',
                              code=SubmitErrorCode.NOT_FOUND)

    @transaction.atomic
    def action(self):
        self._update_pr_users()


class PRLabelUpdated(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist',
                              code=SubmitErrorCode.NOT_FOUND)

    @transaction.atomic
    def action(self):
        self._update_labels()


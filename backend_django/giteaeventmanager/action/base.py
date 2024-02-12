from users.models import GiteaUser
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from experiments.models import Request
from django.db import transaction
from giteaeventmanager.exception import TaskFailure
from helperfunctions.hash import hash_file_sha256
from giteaeventmanager.action.plugin import PullRequestPlugin
from giteaeventmanager.auth import GiteaAuthHandle
from django.conf import settings
import requests

import logging

log = logging.getLogger(__name__)


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
        headers = {'Authorization':
                     f'token {token}'}
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise TaskFailure(f'could not retrieve user data for {username} ({response.status_code}): {response.text}')
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
            creation_date=creation_date,
            last_change_date=last_change_date,
            requester=requester
        )
        request.save()
        request.assignees.set(assignee_users)
        request.reviewers.set(reviewer_users)
        return request

    def _download_and_hash(self):
        downloaded_files, missing_files = self.pullrequest_plugin.download()
        if missing_files:
            self.pullrequest_plugin.cleanup()
            raise TaskFailure(f'missing files for pull request open ({[file.as_posix() for file in missing_files]})')
        self.pullrequest_plugin.check_file_validity()
        self.pullrequest_plugin.hash()

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
        # get request by gitea pr number
        gitea_pr_number = self.data["number"]
        try:
            self.request = Request.objects.get(gitea_pr_number=gitea_pr_number)
        except Request.DoesNotExist:
            raise TaskFailure(f'request for gitea pr number {gitea_pr_number} does not exist')

    @transaction.atomic
    def __db_merge_pr(self):
        self.request.object.published = True
        self.request.object.published_at = self._transform_gitea_date(self.data["pull_request"]["merged_at"])
        self.request.object.published_by = self._get_user(self.data["pull_request"]["merged_by"]["login"])
        self.request.object.save()

    @transaction.atomic
    def __db_delete_pr(self):
        self.request.delete()

    def action(self) -> (bool, str):
        merged = self.data["pull_request"]["merged"]
        if merged:
            self.__db_merge_pr()
        self.__db_delete_pr()


class PRClosedCreate(PRClosed):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        super().check()

    def action(self):
        super().action()


class PROpenedCreate(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                 object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        self._download_and_hash()

        # check if object does already exist
        object_instance = self.pullrequest_plugin.get_object()
        if object_instance:
            raise TaskFailure(f'{self.object_name} already exists')

        # check if object with same content/hash already exists
        existing_object = self.pullrequest_plugin.get_object_by_hash()
        if existing_object:
            raise TaskFailure(f'{self.object_name} with same content already exists')

    def action(self):
        object_instance = self.pullrequest_plugin.update_object(self._get_pr_requester())
        self.request = self._create_pull_request(object_instance)
        self.cleanup()


class PRSynchronizedCreate(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                 object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            log.info(f'request for gitea pr number {self.data["number"]} does not exist')
        self._download_and_hash()

    def action(self):
        self.pullrequest_plugin.update_object(self._get_pr_requester())
        self.cleanup()


class PRReopenedCreate(PROpenedCreate):
    """
    This class is used when a pull request with the action create is reopened.
    The functionality is the same as for PROpenedCreate.
    """

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                    object_name: str):
            super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        super().check()

    def action(self):
        super().action()


class PREdited(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            self._download_and_hash()

    def action(self):
        if not self._request_exists():
            # if the request does not exist, we create it
            object_instance = self.pullrequest_plugin.update_object(self._get_pr_requester())
            self.request = self._create_pull_request(object_instance)
            self.cleanup()


class PRAssigned(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist')

    @transaction.atomic
    def action(self):
        self._update_pr_users()


class PRUnassigned(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist')

    @transaction.atomic
    def action(self):
        self._update_pr_users()


class PRReviewRequested(PullRequest):

    def __init__(self, pullrequest_plugin: PullRequestPlugin, json_data: dict, objective: str, action: str,
                object_name: str):
        super().__init__(pullrequest_plugin, json_data, objective, action, object_name)

    def check(self):
        if not self._request_exists():
            raise TaskFailure(f'request for gitea pr number {self.data["number"]} does not exist')

    @transaction.atomic
    def action(self):
        self._update_pr_users()

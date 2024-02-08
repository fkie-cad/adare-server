from django.conf import settings
import re
import requests
from django.contrib.auth.models import User
from helperfunctions.download import download
from pathlib import Path
from datetime import datetime

import logging
log = logging.getLogger(__name__)


class PullRequest:
    id: int
    title: str
    description: str
    changed_files: dict
    last_commit: str = None

    def __init__(self, json_data, objective: str, action: str, experiment: str, changed_files: list):
        self.id = json_data["number"]
        self.title = json_data["title"]
        self.description = json_data["body"]
        self.objective = objective
        self.action_type = action
        self.experiment = experiment
        self.changed_files = {
            f"{data['filename']}": data for data in changed_files
        }

        # get last commit
        self.last_commit = json_data["head"]["sha"]

    def __str__(self):
        return f'PullRequest(number={self.id}, title={self.title}, description={self.description})'

    def check(self) -> (bool, str):
        # depending on the objective and action execute the corresponding check
        if self.objective == "exp":
            if self.action_type == "create":
                return self.__check_experiment_create()
            # elif self.action == "update":
            #     self.__check_experiment_update()
            # elif self.action == "delete":
            #     self.__check_experiment_delete()
            # elif self.action == "assign":
            #     self.__check_experiment_assign()
            # elif self.action == "unassign":
            #     self.__check_experiment_unassign()
            else:
                log.error(f'unknown action "{self.action}"')
                return False, f'unknown action "{self.action_type}"'
        else:
            log.error(f'unknown objective "{self.objective}"')
            return False, f'unknown objective "{self.objective}"'

    def action(self) -> (bool, str):
        if self.objective == "exp":
            if self.action_type == "create":
                return self.__experiment_create()
            # elif self.action == "update":
            #     self.__check_experiment_update()
            # elif self.action == "delete":
            #     self.__check_experiment_delete()
            # elif self.action == "assign":
            #     self.__check_experiment_assign()
            # elif self.action == "unassign":
            #     self.__check_experiment_unassign()
            else:
                log.error(f'unknown action "{self.action_type}"')
                return False, f'unknown action "{self.action_type}"'
        else:
            log.error(f'unknown objective "{self.objective}"')
            return False, f'unknown objective "{self.objective}"'

    def __experiment_create(self) -> (bool, str):
        """
        Create a new request used to create an experiment.
        """
        # get testset file and action file via gitea api
        testset_file_path = f'experiments/{self.experiment}/{self.experiment}.yml'
        action_file_path = f'experiments/{self.experiment}/{self.experiment}.py'
        config_file_path = f'experiments/{self.experiment}/config.yml'
        testset_file_download_url = f'{settings.GITEA_REPO_API}/raw/{testset_file_path}?ref={self.last_commit}'
        action_file_download_url = f'{settings.GITEA_REPO_API}/raw/{action_file_path}?ref={self.last_commit}'
        config_file_download_url = f'{settings.GITEA_REPO_API}/raw/{config_file_path}?ref={self.last_commit}'

        # create a temporary directory (include timestamp to avoid conflicts)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        Path(f'/tmp/{self.experiment}_{timestamp}').mkdir()

        # download testset file and action file
        download(testset_file_download_url, Path(f'/tmp/{self.experiment}_{timestamp}/{Path(testset_file_path).name}', quiet=True))
        download(action_file_download_url, Path(f'/tmp/{self.experiment}_{timestamp}/{Path(action_file_path).name}', quiet=True))
        download(config_file_download_url, Path(f'/tmp/{self.experiment}_{timestamp}/{Path(config_file_path).name}', quiet=True))

        #


        # remove the downloaded files
        Path(f'/tmp/{Path(testset_file_path).name}').unlink()
        Path(f'/tmp/{Path(action_file_path).name}').unlink()

    def __check_experiment_create(self) -> (bool, str):
        """
        Check if the pull request is an experiment create request.
        This is the case if a new directory in the experiments directory was created and this directory contains the following files:
        - $EXPERIMENT.yml
        - $EXPERIMENT.py
        """
        testset_file = self.changed_files.get(f"experiments/{self.experiment}/{self.experiment}.yml")
        action_file = self.changed_files.get(f"experiments/{self.experiment}/{self.experiment}.py")
        if not testset_file:
            log.error(f'pull request {self.id} is not an experiment create request: {self.experiment}.yml is missing')
            return False, "testset file is missing"
        if not action_file:
            log.error(f'pull request {self.id} is not an experiment create request: {self.experiment}.py is missing')
            return False, "testset file is missing"

        if not testset_file["status"] == "added":
            log.error(f'pull request {self.id} is not an experiment create request: {self.experiment}.yml is not added')
            return False, f"testset file was not added but {testset_file['status']}"

        if not action_file["status"] == "added":
            log.error(f'pull request {self.id} is not an experiment create request: {self.experiment}.py is not added')
            return False, f"testset file was not added but {action_file['status']}"

        return True, ''


def pull_request_opened(request, json_data) -> (bool, str):
    # determine type of the pull request (experiment create, experiment update, experiment delete, experiment assign, experiment unassign) by checking the title
    title = json_data["pull_request"]["title"]
    # parse title as it is in the format "[exp create] <experiment name>"
    pattern = r"\[(?P<objective>\w+) (?P<action>\w+)\] (?P<name>.+)"
    match = re.match(pattern, title)
    if not match:
        log.warning(f'could not parse title "{title}"')
        return False, "could not parse title"

    objective = match.group("objective")
    action = match.group("action")
    experiment = match.group("name")
    # strip whitespaces from experiment name
    experiment = experiment.strip()

    # access the changed files of the pull request by accessing the gitea api
    username = request.user.username
    user = User.objects.get(username=username)
    # get changed files
    url = f'{settings.GITEA_REPO_API}/pulls/{json_data["number"]}/files'
    resp = requests.get(url,
                        headers={
                            'Authorization': f'token {user.socialaccount_set.first().socialtoken_set.first().token}'})

    if resp.status_code == 200:
        changed_files = resp.json()
    else:
        log.error(f'could not get changed files from gitea: {resp.status_code}')
        return False, f'could not get changed files from gitea: {resp.status_code}'

    # create a PullRequest object
    pull_request = PullRequest(json_data, objective, action, experiment, changed_files)
    # execute the check
    success, msg = pull_request.check()
    if not success:
        return success, msg

    success, msg = pull_request.action()
    return success, msg

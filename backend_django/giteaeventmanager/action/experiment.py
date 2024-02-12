from django.conf import settings
from helperfunctions.download import download
from pathlib import Path
from helperfunctions.hash import combine_hashes, hash_file_sha256
from experiments.models import Experiment, Request
from giteaeventmanager.deserialize import create_experiment
from giteaeventmanager.action.base import RequestAction

import logging

log = logging.getLogger(__name__)


class ExperimentRequestAction(RequestAction):
    experiment: str = None
    testset_file: Path = None
    os_info_file: Path = None
    action_file: Path = None

    action_file_remote_url: str = None
    testset_file_remote_url: str = None
    os_info_file_remote_url: str = None

    testset_sha256: str = None
    os_info_sha256: str = None
    action_sha256: str = None
    experiment_sha256: str = None

    def __init__(self, json_data: dict, objective: str, action: str, object_name: str, changed_files: list):
        super().__init__(json_data, objective, action, object_name, changed_files)
        self.experiment = object_name

    def check(self) -> (bool, str):
        pass

    def action(self) -> (bool, str):
        pass


class ExperimentRequestCreateAction(ExperimentRequestAction):

    def __init__(self, json_data: dict, objective: str, action: str, object_name: str, changed_files: list):
        super().__init__(json_data, objective, action, object_name, changed_files)
        self.experiment = object_name

    def check(self) -> (bool, str):
        # download the files
        self.__download_files()
        # check if all files are present
        missing_files = self.__return_missing_experiment_files_complete()
        if missing_files:
            self.__cleanup()
            return False, f'missing files: {", ".join(missing_files)}'
        # hash the files
        self.__hash_experiment_files()
        return True, "success"

    def action(self) -> (bool, str):
        return self.__update_experiment_request()

    def __download_files(self):
        if not self.experiment:
            log.error('no experiment name specified')
            return
        token = self._get_gitea_token()
        # create a temporary directory (include timestamp to avoid conflicts)
        tmp_dir = self._get_tmp_dir()

        # download action file
        action_file_path = f'experiments/{self.experiment}/action.py'
        action_file_remote_url = f'{settings.GITEA_REPO_API}raw/{action_file_path}'
        action_file = tmp_dir / 'action.py'
        success = download(f'{action_file_remote_url}?ref={self.last_commit}', action_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.action_file = action_file
            self.action_file_remote_url = action_file_remote_url

        # download testset file
        testset_file_path = f'experiments/{self.experiment}/testset.yml'
        testset_file_remote_url = f'{settings.GITEA_REPO_API}raw/{testset_file_path}'
        testset_file = tmp_dir / 'testset.yml'
        success = download(f'{testset_file_remote_url}?ref={self.last_commit}', testset_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.testset_file = testset_file
            self.testset_file_remote_url = testset_file_remote_url

        # download os information file
        os_info_file_path = f'experiments/{self.experiment}/os.yml'
        os_info_file_remote_url = f'{settings.GITEA_REPO_API}raw/{os_info_file_path}'
        os_info_file = tmp_dir / 'os.yml'
        success = download(f'{os_info_file_remote_url}?ref={self.last_commit}', os_info_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.os_info_file = os_info_file
            self.os_info_file_remote_url = os_info_file_remote_url

    def __cleanup(self):
        # remove the temporary directory
        if self.action_file:
            if self.action_file.is_file():
                self.action_file.unlink()
                log.info(f'removed action file {self.action_file}')
        if self.testset_file:
            if self.testset_file.is_file():
                self.testset_file.unlink()
                log.info(f'removed testset file {self.testset_file}')
        if self.os_info_file:
            if self.os_info_file.is_file():
                self.os_info_file.unlink()
                log.info(f'removed os information file {self.os_info_file}')

    def __return_missing_experiment_files_complete(self) -> list:
        missing_files = []
        if not self.action_file:
            missing_files.append("action file")
        if not self.testset_file:
            missing_files.append("testset file")
        if not self.os_info_file:
            missing_files.append("os file")
        return missing_files

    def __hash_experiment_files(self):
        self._set_file_sha256('action_file', 'action_sha256')
        self._set_file_sha256('testset_file', 'testset_sha256')
        self._set_file_sha256('os_info_file', 'os_info_sha256')
        # hash all hashes
        if self.action_sha256 and self.testset_sha256 and self.os_info_sha256:
            self.experiment_sha256 = combine_hashes([self.action_sha256, self.testset_sha256, self.os_info_sha256])

    def __update_experiment_request(self) -> (bool, str):
        # get the request by the pull request url
        request = None
        try:
            request = Request.objects.get(gitea_url=self.data["pull_request"]["url"])
            log.info(f'Request with url {self.data["pull_request"]["url"]} does exists')
        except Request.DoesNotExist:
            log.info(f'Request with url {self.data["pull_request"]["url"]} does not exist')

        if request:
            # update/delete the request
            pass
        else:
            # create a new request

            # get experiment by unique hash
            experiment = None
            try:
                experiment = Experiment.objects.get(sha256hash=self.experiment_sha256)
                log.info(f'Experiment with hash {self.experiment_sha256} does exists')
            except Experiment.DoesNotExist:
                log.info(f'Experiment with hash {self.experiment_sha256} does not exist')

            requester, _, _ = self._get_pr_users()

            # if the experiment does not exist, create a new one
            if not experiment:
                experiment = create_experiment(self.os_info_file, self.testset_file, self.experiment, self.description,
                                               requester,
                                               self.experiment_sha256,
                                               self.action_file_remote_url,
                                               self.testset_file_remote_url,
                                               self.os_info_file_remote_url,
                                               self.action_sha256, self.testset_sha256, self.os_info_sha256)
            else:
                # update the experiment
                pass

            # create a new request
            self._create_pull_request(experiment)

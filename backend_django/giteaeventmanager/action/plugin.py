from abc import ABC, abstractmethod
from pathlib import Path

from users.models import GiteaUser
from django.db import transaction

from helperfunctions.download import download
from django.conf import settings
from giteaeventmanager.auth import GiteaAuthHandle
from datetime import datetime
from experiments.models import Requirement as RequirementModel, TestfunctionSet, Request, TestFunction, TestParameter
from giteaeventmanager.exception import TaskFailure
from helperfunctions.requirements import check_if_requirements_file_is_valid, parse_requirements_from_file, Requirement
from helperfunctions.pyfileanalyze.pymoduleanalyzer import PyModuleAnalyzer

from helperfunctions.hash import hash_file_sha256, combine_hashes


import logging
log = logging.getLogger(__name__)


class PullRequestPluginInterface(ABC):

    @abstractmethod
    def download(self) -> (list[Path], list[Path]):
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @abstractmethod
    def hash(self):
        pass

    @abstractmethod
    def get_object(self):
        pass

    @abstractmethod
    def get_object_by_hash(self):
        pass

    @abstractmethod
    def update_object(self, published_by: GiteaUser):
        pass

    @abstractmethod
    def check_file_validity(self):
        pass


class PullRequestPlugin(PullRequestPluginInterface):
    # data from gitea
    objective: str = None
    object_name: str = None
    last_commit: str = None

    # data within the plugin
    tmp_dir: Path = None
    sha256: str = None

    def __init__(self, objective: str, object_name: str, last_commit: str):
        self.objective = objective
        self.object_name = object_name
        self.last_commit = last_commit

    @abstractmethod
    def download(self) -> (list[Path], list[Path]):
        pass

    def cleanup(self):
        # delete all files in tmp dir
        for file in self.tmp_dir.iterdir():
            file.unlink()
        if self.tmp_dir and self.tmp_dir.is_dir():
            self.tmp_dir.rmdir()

    @abstractmethod
    def hash(self):
        pass

    @abstractmethod
    def get_object(self):
        pass

    @abstractmethod
    def get_object_by_hash(self):
        pass

    @abstractmethod
    def update_object(self, published_by: GiteaUser):
        pass

    @abstractmethod
    def check_file_validity(self):
        pass

    def _get_tmp_dir(self) -> Path:
        if self.tmp_dir:
            return self.tmp_dir
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        tmp_dir = Path(f'/tmp/{self.objective}_{timestamp}')
        tmp_dir.mkdir()
        self.tmp_dir = tmp_dir
        return tmp_dir

    def _set_file_sha256(self, file_attribute, hash_attribute):
        file_obj = getattr(self, file_attribute)
        if file_obj and file_obj.is_file():
            setattr(self, hash_attribute, hash_file_sha256(file_obj))


class TestfunctionsetPlugin(PullRequestPlugin):
    tfset_remote_url: str = None
    tfset_sha256: str = None
    tfset_file: Path = None

    tfreq_remote_url: str = None
    tfreq_sha256: str = None
    tfreq_file: Path = None

    def __init__(self, objective: str, object_name: str, last_commit: str):
        super().__init__(objective, object_name, last_commit)

    def download(self) -> (list[Path], list[Path]):
        token = GiteaAuthHandle.get_token()

        downloaded_files = []
        missing_files = []

        tfset_path = f'testfunctions/{self.object_name}/{self.object_name}.py'
        tfset_remote_url = f'{settings.GITEA_REPO_API}raw/{tfset_path}'
        tfset_file = self._get_tmp_dir() / f'{self.object_name}.py'
        success = download(f'{tfset_remote_url}?ref={self.last_commit}', tfset_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.tfset_file = tfset_file
            self.tfset_remote_url = tfset_remote_url
            downloaded_files.append(tfset_file)
        else:
            missing_files.append(tfset_file)

        tfreq_path = f'testfunctions/{self.object_name}/requirements.txt'
        tfreq_remote_url = f'{settings.GITEA_REPO_API}raw/{tfreq_path}'
        tfreq_file = self._get_tmp_dir() / 'requirements.txt'
        success = download(f'{tfreq_remote_url}?ref={self.last_commit}', tfreq_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.tfreq_file = tfreq_file
            self.tfreq_remote_url = tfreq_remote_url
            downloaded_files.append(tfreq_file)
        else:
            missing_files.append(tfreq_file)

        return downloaded_files, missing_files

    def hash(self):
        self._set_file_sha256('tfset_file', 'tfset_sha256')
        self._set_file_sha256('tfreq_file', 'tfreq_sha256')
        self.sha256 = combine_hashes([self.tfset_sha256, self.tfreq_sha256])

    def get_object(self):
        return TestfunctionSet.objects.filter(name=self.object_name).first()

    def get_object_by_hash(self):
        if not self.sha256:
            raise TaskFailure('hash not set')
        return TestfunctionSet.objects.filter(sha256hash=self.sha256).first()

    def check_file_validity(self):
        valid = check_if_requirements_file_is_valid(self.tfreq_file)
        if not valid:
            raise TaskFailure(f'invalid requirements file {self.tfreq_file.as_posix()}')

    def __db_update_requirements(self, requirements: list[Requirement]) -> list[RequirementModel]:
        requirement_objects = []
        for req in requirements:
            RequirementModel.objects.get_or_create(
                package=req.package,
                version=req.version,
                relation=req.relation
            )
            requirement_objects.append(RequirementModel.objects.get(package=req.package, version=req.version, relation=req.relation))

        return requirement_objects

    def __db_create_testfunctionset(self, requirement_objects: list[RequirementModel], published_by: GiteaUser) -> TestfunctionSet:
        tfset = TestfunctionSet(
            name=self.object_name,
            description="",
            sha256hash=self.sha256,
            sha256testfunctionset=self.tfset_sha256,
            sha256requirements=self.tfreq_sha256,
            published_by=published_by,
        )
        tfset.save()
        tfset.requirements.set(requirement_objects)
        return tfset

    def __db_update_testfunctions(self, tfset: TestfunctionSet) -> list[TestFunction]:
        testfunctions: list[TestFunction] = []
        module_analyzer = PyModuleAnalyzer(self.tfset_file)
        for t_func_class in module_analyzer.get_classes(parent='BasicTest'):
            if t_func_class.has_attribute('params'):
                parameter_attr_type = t_func_class.get_attribute('params').get_type()
                matching_parameter_class = module_analyzer.get_class(parameter_attr_type)
                db_parameter_objects = dict()
                if matching_parameter_class:
                    attribute_dict = matching_parameter_class.get_attributes_as_dict()
                    # add parameters to database
                    for attr in attribute_dict.values():
                        testparameter_query = TestParameter.objects.filter(name=attr['name'])
                        db_testparameter_objects = list(testparameter_query)
                        if not db_testparameter_objects:
                            db_testparameter_obj = TestParameter(name=attr['name'], dtype=attr['type'])
                            db_testparameter_obj.save()
                        else:
                            db_testparameter_obj = db_testparameter_objects[0]
                        db_parameter_objects[attr['name']] = db_testparameter_obj

                    # add testfunction to db
                    test_name = t_func_class.get_attribute('testname').get_value()
                    test_description = t_func_class.get_attribute('testdescription').get_value()
                    testfunction_obj = TestFunction.objects.filter(name=t_func_class.name).first()
                    if testfunction_obj:
                        if testfunction_obj.name != test_name:
                            testfunction_obj.name = test_name
                            log.info(
                                f'test function name of test function class {t_func_class.name} changed to {test_name}')
                        if testfunction_obj.description != test_description:
                            testfunction_obj.description = test_description
                            log.info(
                                f'test description of test function class {t_func_class.name} changed to {test_description}')
                    else:
                        testfunction_obj = TestFunction(type=test_name,
                                                        name=t_func_class.name,
                                                        description=test_description,
                                                        testfunction_set=tfset)
                        testfunction_obj.save()

                    # add parameter to testfunction in database
                    for db_para_obj in db_parameter_objects.values():
                        testfunction_obj.possible_parameters.add(db_para_obj)

                    testfunctions.append(testfunction_obj)
                else:
                    raise TaskFailure(f'parameter class for testfunction class {t_func_class.name} is missing')
            else:
                raise TaskFailure(f'testfunction class {t_func_class.name} is missing the mandatory params attribute')
        return testfunctions

    @transaction.atomic
    def update_object(self, published_by: GiteaUser) -> TestfunctionSet:
        # parse requirements from file
        requirements: list[Requirement] = parse_requirements_from_file(self.tfreq_file)

        requirement_objects = self.__db_update_requirements(requirements)

        tfset = self.__db_create_testfunctionset(requirement_objects, published_by)

        # create testfunctionset object
        self.__db_update_testfunctions(tfset)

        return tfset

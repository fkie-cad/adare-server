from abc import abstractmethod
from pathlib import Path
from helperfunctions.download import download
from django.conf import settings

from giteaeventmanager.action.base import PullRequest
from helperfunctions.hash import hash_file_sha256, combine_hashes
from helperfunctions.requirements import check_if_requirements_file_is_valid, parse_requirements_from_file, Requirement
from experiments.models import Requirement as RequirementModel, TestfunctionSet, Request, TestFunction, TestParameter
from giteaeventmanager.exception import TaskFailure
from pathlib import Path
from helperfunctions.pyfileanalyze.pymoduleanalyzer import PyModuleAnalyzer
from django.db import transaction

import logging

log = logging.getLogger(__name__)


class TestfunctionsetPR(PullRequest):
    tfset: str = None

    def __init__(self, json_data: dict, objective: str, action: str, object_name: str, changed_files: list):
        super().__init__(json_data, objective, action, object_name, changed_files)
        self.tfset = object_name

    @abstractmethod
    def check(self) -> (bool, str):
        pass

    @abstractmethod
    def action(self) -> (bool, str):
        pass


class TestfunctionsetPROpen(TestfunctionsetPR):
    tfset_remote_url: str = None
    tfset_sha256: str = None
    tfset_file: Path = None

    tfreq_remote_url: str = None
    tfreq_sha256: str = None
    tfreq_file: Path = None

    sha256: str = None

    def __init__(self, json_data: dict, objective: str, action: str, object_name: str, changed_files: list):
        super().__init__(json_data, objective, action, object_name, changed_files)

    def check(self) -> (bool, str):
        self.__download_testfunctionset_files()
        missing_files = self._return_missing_files([self.tfset_file, self.tfreq_file])
        if missing_files:
            self._cleanup([self.tfset_file, self.tfreq_file])
            raise TaskFailure(f'missing files for testfunction create ({[file.as_posix() for file in missing_files]})')
        self.__hash_files()

        # check if testfunctionset does already exist
        tfset_query = TestfunctionSet.objects.filter(name=self.tfset)
        if tfset_query:
            tfset = tfset_query[0]
            if tfset.sha256hash == self.sha256:
                raise TaskFailure(f'testfunctionset {self.tfset} already exists')
            else:
                raise TaskFailure(f'testfunctionset {self.tfset} already exists but has different content')

    def action(self) -> (bool, str):
        self.__create_testfunctionset()

    def __download_testfunctionset_files(self):
        token = self._get_gitea_token()

        tfset_path = f'testfunctions/{self.tfset}/{self.tfset}.py'
        tfset_remote_url = f'{settings.GITEA_REPO_API}raw/{tfset_path}'
        tfset_file = self._get_tmp_dir() / f'{self.tfset}.py'
        success = download(f'{tfset_remote_url}?ref={self.last_commit}', tfset_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.tfset_file = tfset_file
            self.tfset_remote_url = tfset_remote_url

        tfreq_path = f'testfunctions/{self.tfset}/requirements.txt'
        tfreq_remote_url = f'{settings.GITEA_REPO_API}raw/{tfreq_path}'
        tfreq_file = self._get_tmp_dir() / 'requirements.txt'
        success = download(f'{tfreq_remote_url}?ref={self.last_commit}', tfreq_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.tfreq_file = tfreq_file
            self.tfreq_remote_url = tfreq_remote_url

    def __hash_files(self):
        self._set_file_sha256('tfset_file', 'tfset_sha256')
        self._set_file_sha256('tfreq_file', 'tfreq_sha256')
        self.sha256 = combine_hashes([self.tfset_sha256, self.tfreq_sha256])

    def __db_create_requirements(self, requirements: list[Requirement]) -> list[RequirementModel]:
        requirement_objects = [
            RequirementModel(
                package=req.package,
                version=req.version,
                relation=req.relation
            ) for req in requirements
        ]

        # save requirement objects
        for req in requirement_objects:
            req.save()

        return requirement_objects

    def __db_create_testfunctionset(self, requirement_objects: list[RequirementModel]) -> TestfunctionSet:
        tfset = TestfunctionSet(
            name=self.tfset,
            description="",
            sha256hash=self.sha256,
            sha256testfunctionset=self.tfset_sha256,
            sha256requirements=self.tfreq_sha256
        )
        tfset.save()
        tfset.requirements.set(requirement_objects)
        return tfset

    def __db_create_request(self, tfset: TestfunctionSet):
        return self._create_pull_request(tfset)

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
    def __create_testfunctionset(self):
        # parse requirements from file
        requirements: list[Requirement] = parse_requirements_from_file(self.tfreq_file)

        requirement_objects = self.__db_create_requirements(requirements)

        tfset = self.__db_create_testfunctionset(requirement_objects)

        # create testfunctionset object
        self.__db_update_testfunctions(tfset)

        # create the request for the testfunctionset
        self.__db_create_request(tfset)


class TestfunctionsetPREdit(TestfunctionsetPR):
    tfset_remote_url: str = None
    tfset_sha256: str = None
    tfset_file: Path = None

    tfreq_remote_url: str = None
    tfreq_sha256: str = None
    tfreq_file: Path = None

    sha256: str = None

    def __init__(self, json_data: dict, objective: str, action: str, object_name: str, changed_files: list):
        super().__init__(json_data, objective, action, object_name, changed_files)

    def check(self) -> (bool, str):
        pass

    def action(self) -> (bool, str):
        pass


from abc import ABC, abstractmethod
from pathlib import Path

from users.models import GiteaUser
from django.db import transaction

from helperfunctions.download import download
from django.conf import settings
from giteaeventmanager.auth import GiteaAuthHandle
from datetime import datetime
from experiments.models import Requirement as RequirementModel, TestfunctionSet, TestFunction, TestParameter, \
    Experiment, Tool, AbstractTest, TestParameterEntry, Environment, OsInfo
from giteaeventmanager.exception import TaskFailure
from helperfunctions.requirements import check_if_requirements_file_is_valid, parse_requirements_from_file, Requirement
from helperfunctions.pyfileanalyze.pymoduleanalyzer import PyModuleAnalyzer
from testsetfile.fileformat import FTestsetFile, FTest, FToolTest
from testsetfile.parser import parse_testsetfile
from helperfunctions.yaml import yaml_to_dict

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
    def delete_object(self):
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

    def delete_object(self):
        obj = self.get_object()
        if obj:
            obj.delete()

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
        if self.tfset_sha256 and self.tfreq_sha256:
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
            requirement_objects.append(
                RequirementModel.objects.get(package=req.package, version=req.version, relation=req.relation))

        return requirement_objects

    def __db_create_testfunctionset(self, requirement_objects: list[RequirementModel],
                                    published_by: GiteaUser) -> TestfunctionSet:
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
                        testfunction_obj = TestFunction(type=t_func_class.name,
                                                        name=test_name,
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


class ExperimentPlugin(PullRequestPlugin):
    action_file: Path = None
    actionfile_remote_url: str = None
    action_sha256: str = None

    testset_file: Path = None
    testset_file_remote_url: str = None
    testset_sha256: str = None

    metadata_file: Path = None
    metadata_file_remote_url: str = None

    def __init__(self, objective: str, object_name: str, last_commit: str):
        super().__init__(objective, object_name, last_commit)

    def download(self) -> (list[Path], list[Path]):
        token = GiteaAuthHandle.get_token()

        downloaded_files = []
        missing_files = []

        action_path = f'experiments/{self.object_name}/action.py'
        actionfile_remote_url = f'{settings.GITEA_REPO_API}raw/{action_path}'
        action_file = self._get_tmp_dir() / 'action.py'
        success = download(f'{actionfile_remote_url}?ref={self.last_commit}', action_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.action_file = action_file
            self.actionfile_remote_url = actionfile_remote_url
            downloaded_files.append(action_file)
        else:
            missing_files.append(action_file)

        testset_path = f'experiments/{self.object_name}/testset.yml'
        testset_file_remote_url = f'{settings.GITEA_REPO_API}raw/{testset_path}'
        testset_file = self._get_tmp_dir() / 'testset.yml'
        success = download(f'{testset_file_remote_url}?ref={self.last_commit}', testset_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.testset_file = testset_file
            self.testset_file_remote_url = testset_file_remote_url
            downloaded_files.append(testset_file)
        else:
            missing_files.append(testset_file)

        metadata_path = f'experiments/{self.object_name}/metadata.yml'
        metadata_file_remote_url = f'{settings.GITEA_REPO_API}raw/{metadata_path}'
        metadata_file = self._get_tmp_dir() / 'metadata.yml'
        success = download(f'{metadata_file_remote_url}?ref={self.last_commit}', metadata_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.metadata_file = metadata_file
            self.metadata_file_remote_url = metadata_file_remote_url
            downloaded_files.append(metadata_file)
        else:
            missing_files.append(metadata_file)

        return downloaded_files, missing_files

    def hash(self):
        self._set_file_sha256('action_file', 'action_sha256')
        self._set_file_sha256('testset_file', 'testset_sha256')
        if self.action_sha256 and self.testset_sha256:
            self.sha256 = combine_hashes([self.action_sha256, self.testset_sha256])

    def get_object(self):
        return Experiment.objects.filter(name=self.object_name).first()

    def get_object_by_hash(self):
        return Experiment.objects.filter(sha256hash=self.sha256).first()

    def __db_get_abstract_test(self, test: FTest, tool: Tool = None) -> AbstractTest or None:
        testfunction = TestFunction.objects.filter(name=test.type).first()
        if not testfunction:
            raise TaskFailure(f'test function {test.type} does not exist')

        parameter_entries = []
        for p_key, p_val in test.params.items():
            parameter = TestParameter.objects.filter(name=p_key).first()
            # check if TestParameterEntry already exists
            test_parameter_entry_q = TestParameterEntry.objects.filter(parameter=parameter, value=str(p_val))
            test_parameter_entry_obj = test_parameter_entry_q.first()
            if not test_parameter_entry_obj:
                # create an TestParameterEntry object for the parameter
                test_parameter_entry_obj = TestParameterEntry(parameter=parameter, value=str(p_val))
                test_parameter_entry_obj.save()
            parameter_entries.append(test_parameter_entry_obj)

        # check if abstract test already exists (todo: make this more efficient by using filter instead of filtering in python)
        abstract_test_obj = None
        if tool:
            abstract_test_q = AbstractTest.objects.filter(name=test.name, description=test.description,
                                                          testfunction=testfunction, tool=tool)
        else:
            abstract_test_q = AbstractTest.objects.filter(name=test.name, description=test.description,
                                                          testfunction=testfunction)
        # check if all parameter entries are in the abstract test and vice versa by their ids
        parameter_entry_ids_data = [p.id for p in parameter_entries]
        for abstract_test in abstract_test_q.all():
            # check if all parameter entries are in the abstract test
            parameter_entry_ids_abstract_test = [p.id for p in abstract_test.parameters]
            if set(parameter_entry_ids_data) == set(parameter_entry_ids_abstract_test):
                abstract_test_obj = abstract_test

        # if abstract test does not exist, create it
        if not abstract_test_obj:
            abstract_test_obj = AbstractTest(name=test.name, description=test.description, testfunction=testfunction,
                                             tool=tool)

            # add parameter entries to abstract test
            for parameter_entry in parameter_entries:
                # add parameter entry to abstract test
                abstract_test_obj.parameters.add(parameter_entry)

            abstract_test_obj.save()

        return abstract_test_obj

    def __db_get_tool(self, name: str, command: str):
        """
            Get/Creates the tool from the tool data.
        """
        tool = Tool.objects.filter(name=name, command=command).first()
        if not tool:
            tool = Tool(name=name, command=command)
            tool.save()
        return tool

    def __db_create_abstracttests_from_testsetfile(self, testset_file_path: Path):
        testset: FTestsetFile = parse_testsetfile(testset_file_path)

        abstract_tests = []
        for test in testset.tests:
            if isinstance(test, FTest):
                abstract_test = self.__db_get_abstract_test(test)
                abstract_tests.append(abstract_test)
            elif isinstance(test, FToolTest):
                tool = self.__db_get_tool(test.tool, test.command)
                for inner_test in test.tests:
                    abstract_test = self.__db_get_abstract_test(inner_test, tool=tool)
                    abstract_tests.append(abstract_test)
            else:
                raise TaskFailure(f'unknown test type {type(test)}')

        return abstract_tests

    @transaction.atomic
    def __db_create_experiment(self, metadata_file: Path, testset_file: Path, experiment_name: str,
                               experiment_description: str,
                               user: GiteaUser, experiment_sha256: str, action_file_remote_url: str,
                               testset_file_remote_url: str,
                               metadata_remote_url: str,
                               action_sha256: str, testset_sha256: str):

        # deserialize the metadata file
        metadata = yaml_to_dict(metadata_file)
        environments = []
        for env in metadata['environments']:
            env_instance = Environment.objects.filter(name=env).first()
            if not env_instance:
                raise TaskFailure(f'environment {env["name"]} does not exist')
            environments.append(env_instance)

        # deserialize the testset file
        abstract_tests = self.__db_create_abstracttests_from_testsetfile(testset_file)
        log.info('retrieved abstract tests from testset file')

        # create experiment object
        experiment = Experiment(
            name=experiment_name,
            description=experiment_description,
            action_file=action_file_remote_url,
            testset_file=testset_file_remote_url,
            metadata_file=metadata_remote_url,

            published_by=user,

            sha256hash=experiment_sha256,
            sha256action=action_sha256,
            sha256testset=testset_sha256,
        )
        experiment.save()
        experiment.environments.set(environments)
        experiment.abstract_tests.set(abstract_tests)
        log.info(f'created new experiment {experiment}')

        return experiment

    def update_object(self, published_by: GiteaUser):
        experiment = self.__db_create_experiment(self.metadata_file, self.testset_file, self.object_name, "",
                                                 published_by, self.sha256, self.actionfile_remote_url,
                                                 self.testset_file_remote_url, self.metadata_file_remote_url,
                                                 self.action_sha256, self.testset_sha256)
        return experiment

    def check_file_validity(self):
        pass


class EnvironmentPlugin(PullRequestPlugin):
    environment_file: Path = None
    environment_file_remote_url: str = None

    def download(self) -> (list[Path], list[Path]):
        token = GiteaAuthHandle.get_token()

        downloaded_files = []
        missing_files = []

        environment_path = f'environments/{self.object_name}.yml'
        environment_file_remote_url = f'{settings.GITEA_REPO_API}raw/{environment_path}'
        environment_file = self._get_tmp_dir() / f'{self.object_name}.yml'
        success = download(f'{environment_file_remote_url}?ref={self.last_commit}', environment_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.environment_file = environment_file
            self.environment_file_remote_url = environment_file_remote_url
            downloaded_files.append(environment_file)
        else:
            missing_files.append(environment_file)

        return downloaded_files, missing_files

    def hash(self):
        self._set_file_sha256('environment_file', 'sha256')

    def get_object(self):
        return Environment.objects.filter(name=self.object_name).first()

    def get_object_by_hash(self):
        return Environment.objects.filter(sha256hash=self.sha256).first()

    @transaction.atomic
    def __db_create_environment(self, published_by: GiteaUser):
        # deserialize the environment file
        environment_data = yaml_to_dict(self.environment_file)

        # create os_info object
        os_info, created = OsInfo.objects.get_or_create(
            os=environment_data['os']['os'],
            distribution=environment_data['os']['distribution'],
            version=environment_data['os']['version'],
            language=environment_data['os']['language'] if 'language' in environment_data['os'] else None,
            architecture=environment_data['os']['architecture'] if 'architecture' in environment_data['os'] else None,
            details=environment_data['os']['details'] if 'details' in environment_data['os'] else None,
        )

        # create environment object
        environment = Environment(
            name=self.object_name,
            vagrantbox=environment_data['vagrantbox'],
            description=environment_data['description'] if 'description' in environment_data else None,
            os_info=os_info,
            sha256hash=self.sha256,
            published_by=published_by,
        )
        environment.save()
        return environment

    def update_object(self, published_by: GiteaUser):
        environment = self.__db_create_environment(published_by)
        return environment

    def check_file_validity(self):
        # todo: implement check if file is valid (use code as in adare)
        environment_data = yaml_to_dict(self.environment_file)
        if environment_data['name'] != self.object_name:
            raise TaskFailure(f'environment file name {environment_data["name"]} does not match object name {self.object_name}')


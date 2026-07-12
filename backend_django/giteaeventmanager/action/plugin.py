import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse
import requests
from users.models import GiteaUser
from django.db import transaction

from helperfunctions.download import download
from django.conf import settings
from giteaeventmanager.auth import GiteaAuthHandle
from django.utils import timezone
from experiments.models import Requirement as RequirementModel, TestfunctionSet, TestFunction, TestParameter, \
    Experiment, Tool, AbstractTest, TestParameterEntry, Environment, OsInfo, Tag, TagScope, PostSetupInstallation, \
    Recipe
from giteaeventmanager.exception import TaskFailure
from helperfunctions.requirements import check_if_requirements_file_is_valid, parse_requirements_from_file, Requirement
from helperfunctions.pyfileanalyze.pymoduleanalyzer import PyModuleAnalyzer
from testsetfile.fileformat import FTestsetFile, FTest
from testsetfile.parser import parse_playbook_tests
from helperfunctions.yaml import yaml_to_dict

from helperfunctions.hash import hash_file_sha256, combine_hashes

import logging

log = logging.getLogger(__name__)

# sha256 as emitted for `recipe.iso_sha256` / `vm_sha256`: 64 lowercase hex chars
# (validated case-insensitively, matching the client's hash_file_sha256 output).
SHA256_HEX_RE = re.compile(r'^[0-9a-fA-F]{64}$')
# Plausible baked-VM disk extensions accepted for a published `vm` URL.
BAKED_VM_EXTENSIONS = ('.ova', '.qcow2', '.vmdk', '.vdi', '.img')


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
        # idempotent: safe to call multiple times and when nothing was downloaded
        if not self.tmp_dir:
            return
        if self.tmp_dir.is_dir():
            for file in self.tmp_dir.iterdir():
                file.unlink()
            self.tmp_dir.rmdir()
        self.tmp_dir = None

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
        # unique per instance so concurrent / back-to-back ingests never collide
        self.tmp_dir = Path(tempfile.mkdtemp(prefix=f'{self.objective}_'))
        return self.tmp_dir

    def _set_file_sha256(self, file_attribute, hash_attribute):
        file_obj = getattr(self, file_attribute)
        if file_obj and file_obj.is_file():
            setattr(self, hash_attribute, hash_file_sha256(file_obj))

    @staticmethod
    def _create_tags_from_list(tags):
        """Parse tag strings (optionally 'scope:value') into Tag objects."""
        tag_objects = []
        if not tags:
            return tag_objects
        for tag in tags:
            if not tag:
                continue
            if ':' in tag:
                scope_name, value = tag.split(':', 1)
                scope = TagScope.objects.filter(name=scope_name).first()
                if scope:
                    obj, _ = Tag.objects.get_or_create(scope=scope, value=value)
                else:
                    obj, _ = Tag.objects.get_or_create(scope=None, value=tag)
            else:
                obj, _ = Tag.objects.get_or_create(scope=None, value=tag)
            tag_objects.append(obj)
        return tag_objects


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
            file=self.tfset_remote_url,
            requirements_file=self.tfreq_remote_url,
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
    playbook_file: Path = None
    playbookfile_remote_url: str = None
    playbook_sha256: str = None

    metadata_file: Path = None
    metadata_file_remote_url: str = None
    metadata_sha256: str = None

    def __init__(self, objective: str, object_name: str, last_commit: str):
        super().__init__(objective, object_name, last_commit)

    def download(self) -> (list[Path], list[Path]):
        token = GiteaAuthHandle.get_token()

        downloaded_files = []
        missing_files = []

        playbook_path = f'experiments/{self.object_name}/playbook.yml'
        playbookfile_remote_url = f'{settings.GITEA_REPO_API}raw/{playbook_path}'
        playbook_file = self._get_tmp_dir() / 'playbook.yml'
        success = download(f'{playbookfile_remote_url}?ref={self.last_commit}', playbook_file, quiet=True,
                           response_codes_error=[404], token=token)
        if success:
            self.playbook_file = playbook_file
            self.playbookfile_remote_url = playbookfile_remote_url
            downloaded_files.append(playbook_file)
        else:
            missing_files.append(playbook_file)

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
        self._set_file_sha256('playbook_file', 'playbook_sha256')
        self._set_file_sha256('metadata_file', 'metadata_sha256')
        if self.playbook_sha256 and self.metadata_sha256:
            self.sha256 = combine_hashes([self.playbook_sha256, self.metadata_sha256])

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
        abstract_test_q = AbstractTest.objects.filter(name=test.name, description=test.description,
                                                      testfunction=testfunction)
        if tool:
            abstract_test_q = abstract_test_q.filter(tools=tool)
        # check if all parameter entries are in the abstract test and vice versa by their ids
        parameter_entry_ids_data = [p.id for p in parameter_entries]
        for abstract_test in abstract_test_q.all():
            # check if all parameter entries are in the abstract test
            parameter_entry_ids_abstract_test = [p.id for p in abstract_test.parameters.all()]
            if set(parameter_entry_ids_data) == set(parameter_entry_ids_abstract_test):
                abstract_test_obj = abstract_test

        # if abstract test does not exist, create it
        if not abstract_test_obj:
            abstract_test_obj = AbstractTest(name=test.name, description=test.description, testfunction=testfunction)
            abstract_test_obj.save()

            if tool:
                abstract_test_obj.tools.add(tool)

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

    def __db_create_abstracttests_from_playbook(self, playbook_file_path: Path):
        testset: FTestsetFile = parse_playbook_tests(playbook_file_path, self.object_name)

        abstract_tests = []
        for test in testset.tests:
            if isinstance(test, FTest):
                abstract_test = self.__db_get_abstract_test(test)
                abstract_tests.append(abstract_test)
            else:
                raise TaskFailure(f'unknown test type {type(test)}')

        return abstract_tests

    @transaction.atomic
    def __db_create_experiment(self, metadata_file: Path, playbook_file: Path, experiment_name: str,
                               experiment_description: str,
                               user: GiteaUser, experiment_sha256: str, playbook_file_remote_url: str,
                               metadata_remote_url: str,
                               playbook_sha256: str):

        # deserialize the metadata file
        metadata = yaml_to_dict(metadata_file)
        environments = []
        for env in metadata['environments']:
            env_instance = Environment.objects.filter(name=env).first()
            if not env_instance:
                raise TaskFailure(f'environment {env} does not exist')
            environments.append(env_instance)

        # deserialize the tests embedded in the playbook file
        abstract_tests = self.__db_create_abstracttests_from_playbook(playbook_file)
        log.info('retrieved abstract tests from playbook file')

        # create tags
        tag_objects = self._create_tags_from_list(metadata.get('tags'))

        # create experiment object
        experiment = Experiment(
            name=experiment_name,
            description=experiment_description,
            playbook_file=playbook_file_remote_url,
            metadata_file=metadata_remote_url,
            bibtex_file=None,
            markdown_file=None,

            published_by=user,

            sha256hash=experiment_sha256,
            sha256playbook=playbook_sha256,
        )
        experiment.save()
        experiment.environments.set(environments)
        experiment.abstract_tests.set(abstract_tests)
        experiment.tags.set(tag_objects)
        log.info(f'created new experiment {experiment}')

        return experiment

    def update_object(self, published_by: GiteaUser):
        experiment = self.__db_create_experiment(self.metadata_file, self.playbook_file, self.object_name, "",
                                                 published_by, self.sha256, self.playbookfile_remote_url,
                                                 self.metadata_file_remote_url, self.playbook_sha256)
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
        # deserialize the environment file (already schema-checked by check_file_validity)
        environment_data = yaml_to_dict(self.environment_file)

        # Select the VM source. Legacy `vagrantbox` (owner/box) is verified against
        # Vagrant Cloud; the modern `vm` source is either an OVA path (local, reference-only)
        # or a published http(s) URL (verified reachable below); `recipe` is a built-on-load
        # ('tutorial') source with no VM to check. check_file_validity guarantees exactly one
        # of these three is present.
        vagrantbox = environment_data.get('vagrantbox') or ''
        vm = environment_data.get('vm') or ''
        vm_sha256 = environment_data.get('vm_sha256') or ''
        recipe_block = environment_data.get('recipe') or {}
        if vagrantbox:
            if '/' not in vagrantbox:
                raise TaskFailure(f'vagrant box {vagrantbox} has not the format owner/box')
            owner, box = vagrantbox.split('/', 1)
            url = f'https://vagrantcloud.com/api/v2/box/{owner}/{box}'
            try:
                response = requests.get(url, timeout=10)
            except requests.RequestException as e:
                raise TaskFailure(f'could not reach vagrant cloud to verify box {vagrantbox}: {e}') from e
            if response.status_code != 200:
                raise TaskFailure(f'vagrant box {vagrantbox} does not exist in vagrant cloud')
        elif vm:
            # A bare local path (vm_type path) is reference-only and not publishable;
            # check_file_validity already rejected non-http(s) vm at validity time, but
            # only a published URL reaches here for a create.
            try:
                response = requests.head(vm, timeout=10, allow_redirects=True)
            except requests.RequestException as e:
                raise TaskFailure(f'could not reach baked VM URL {vm}: {e}') from e
            if response.status_code >= 400:
                raise TaskFailure(f'baked VM URL {vm} is unreachable (status {response.status_code})')

        # create os_info object (os/platform/distribution validated; rest optional)
        os_data = environment_data.get('os') or {}
        os_info, _ = OsInfo.objects.get_or_create(
            os=os_data.get('os'),
            distribution=os_data.get('distribution'),
            platform=os_data.get('platform') or '',
            version=os_data.get('version'),
            language=os_data.get('language'),
            architecture=os_data.get('architecture'),
            details=os_data.get('details'),
        )

        # create tags
        tag_objects = self._create_tags_from_list(environment_data.get('tags'))

        # create postsetupinstallation objects
        post_setup_installation_objects = []
        for installation in environment_data.get('postsetupinstallations') or []:
            name = installation.get('name')
            command = installation.get('command')
            if not name or not command:
                raise TaskFailure("each postsetupinstallation requires 'name' and 'command'")
            obj, _ = PostSetupInstallation.objects.get_or_create(
                name=name,
                command=command,
                description=installation.get('description') or '',
                shell=bool(installation.get('shell', False)),
                cwd=installation.get('cwd') or '',
            )
            post_setup_installation_objects.append(obj)

        # create the recipe object (env-specific: always a fresh row, never shared)
        recipe = None
        if recipe_block:
            params = recipe_block.get('params') or {}
            disk_size = params.get('disk_size')
            recipe = Recipe.objects.create(
                profile=recipe_block.get('profile'),
                iso=recipe_block.get('iso'),
                iso_sha256=recipe_block.get('iso_sha256'),
                template=recipe_block.get('template') or '',
                setup_level=params.get('setup_level'),
                disk_size='' if disk_size is None else str(disk_size),
                ram_mb=params.get('ram_mb'),
                cpus=params.get('cpus'),
                arch=params.get('arch') or '',
            )

        # create environment object; the filename stem is authoritative for the name
        environment = Environment(
            name=self.object_name,
            vm=vm,
            vm_sha256=vm_sha256,
            vagrantbox=vagrantbox,
            recipe=recipe,
            file=self.environment_file_remote_url,
            description=environment_data.get('description') or '',
            os_info=os_info,
            sha256hash=self.sha256,
            published_by=published_by,
        )
        environment.save()
        environment.tags.set(tag_objects)
        environment.post_setup_installations.set(post_setup_installation_objects)
        return environment

    def update_object(self, published_by: GiteaUser):
        environment = self.__db_create_environment(published_by)
        return environment

    def check_file_validity(self):
        """Validate the environment file against the client's EnvironmentMetadata rules.

        The filename stem (``self.object_name``) is authoritative for the
        environment name, so any in-file ``name`` is ignored (matching the adare
        client, ``adare/adare/adare/types/environment.py``). Any failure is raised
        as ``TaskFailure`` so the ingest view returns a clean 400, not a 500.
        """
        environment_data = yaml_to_dict(self.environment_file)

        has_vm = bool(environment_data.get('vm'))
        has_vagrantbox = bool(environment_data.get('vagrantbox'))
        has_recipe = bool(environment_data.get('recipe'))

        # require exactly one source
        num_sources = sum((has_vm, has_vagrantbox, has_recipe))
        if num_sources > 1:
            raise TaskFailure(
                "environment file must specify exactly one VM source, but found "
                "more than one of 'vm', 'vagrantbox' and 'recipe'")
        if num_sources == 0:
            raise TaskFailure(
                "environment file must specify a VM source: one of 'vm' (OVA path), "
                "'recipe' (built-on-load), or legacy 'vagrantbox'")

        if has_recipe:
            recipe_block = environment_data.get('recipe') or {}
            if not isinstance(recipe_block, dict):
                raise TaskFailure("environment 'recipe' block must be a mapping")
            for key in ('profile', 'iso', 'iso_sha256'):
                if not recipe_block.get(key):
                    raise TaskFailure(f"environment 'recipe' block is missing required key '{key}'")
            iso_sha256 = recipe_block.get('iso_sha256')
            if not SHA256_HEX_RE.match(iso_sha256):
                raise TaskFailure(f"recipe 'iso_sha256' is not a valid sha256 hex digest: {iso_sha256!r}")

        if has_vm:
            vm = environment_data.get('vm')
            parsed_vm = urlparse(vm)
            if parsed_vm.scheme not in ('http', 'https'):
                raise TaskFailure(
                    f"'vm' must be an http(s) URL to publish a baked environment (got {vm!r}); "
                    "host the disk image and provide its URL")
            if not parsed_vm.path.lower().endswith(BAKED_VM_EXTENSIONS):
                raise TaskFailure(
                    f"'vm' URL must end in a plausible disk extension {BAKED_VM_EXTENSIONS} (got {vm!r})")
            vm_sha256 = environment_data.get('vm_sha256')
            if not vm_sha256 or not SHA256_HEX_RE.match(vm_sha256):
                raise TaskFailure(f"'vm_sha256' is required for a baked 'vm' URL and must be a valid sha256 hex digest: {vm_sha256!r}")

        # The Environment model requires an os_info relation, so a storable
        # environment must carry an 'os' block with the mandatory OsInfo keys.
        os_block = environment_data.get('os')
        if not isinstance(os_block, dict):
            raise TaskFailure("environment file is missing the required 'os' block")
        for key in ('os', 'platform', 'distribution'):
            if not os_block.get(key):
                raise TaskFailure(f"environment 'os' block is missing required key '{key}'")

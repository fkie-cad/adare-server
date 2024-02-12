from pathlib import Path
from helperfunctions.pyfileanalyze.pymoduleanalyzer import PyModuleAnalyzer
from experiments.models import Experiment, OsInfo, TestParameter, TestFunction, Tool, AbstractTest, TestParameterEntry, TestfunctionSet
from testsetfile.fileformat import FTestsetFile, FTest, FToolTest
from testsetfile.parser import parse_testsetfile
from helperfunctions.yaml import yaml_to_dict
from django.contrib.auth.models import User
from django.db import transaction

import logging

log = logging.getLogger(__name__)


def get_abstract_test(test: FTest, tool: Tool = None) -> AbstractTest or None:
    testfunction = TestFunction.objects.filter(name=test.type).first()
    if not testfunction:
        log.error(f'testfunction {test.type} does not exist')
        return

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
            abstract_test_obj.parameters.append(parameter_entry)

        abstract_test_obj.save()

    return abstract_test_obj


def get_tool(name: str, command: str):
    """
        Get/Creates the tool from the tool data.
    """
    tool = Tool.objects.filter(name=name, command=command).first()
    if not tool:
        tool = Tool(name=name, command=command)
        tool.save()
    return tool


def create_abstracttests_from_testsetfile(testset_file_path: Path):
    testset: FTestsetFile = parse_testsetfile(testset_file_path)

    abstract_tests = []
    for test in testset.tests:
        if type(test) == FTest:
            abstract_test = get_abstract_test(test)
            abstract_tests.append(abstract_test)
        elif type(test) == FToolTest:
            tool = get_tool(test.tool, test.command)
            for inner_test in test.tests:
                abstract_test = get_abstract_test(inner_test, tool=tool)
                abstract_tests.append(abstract_test)
        else:
            log.error(f'unknown test type {type(test)}')

    return abstract_tests


def create_experiment(os_info_file: Path, testset_file: Path, experiment_name: str, experiment_description: str,
                      user: User, experiment_sha256: str, action_file_remote_url: str, testset_file_remote_url: str,
                      os_file_remote_url: str,
                      action_sha256: str, testset_sha256: str, os_info_sha256: str):
    os_info_data = yaml_to_dict(os_info_file)
    # try to serialize the os information
    try:
        os_info, created = OsInfo.objects.get_or_create(**os_info_data)
        if created:
            log.info(f'created new os information {os_info}')
    except (TypeError, ValueError) as e:
        log.error(f'could not serialize os information file {os_info_file}')
        return None, f'could not serialize os information file {os_info_file}'

    # deserialize the testset file
    abstract_tests = create_abstracttests_from_testsetfile(testset_file)
    log.info('retrieved abstract tests from testset file')

    # create experiment object
    experiment = Experiment(
        name=experiment_name,
        description=experiment_description,
        action_file=action_file_remote_url,
        testset_file=testset_file_remote_url,
        os_file=os_file_remote_url,

        os_info=os_info,
        publisher=user,
        published=False,

        sha256hash=experiment_sha256,
        sha256action=action_sha256,
        sha256testset=testset_sha256,
        sha256os=os_info_sha256
    )
    experiment.abstract_tests.set(abstract_tests)
    experiment.save()
    log.info(f'created new experiment {experiment}')

    return experiment, ''

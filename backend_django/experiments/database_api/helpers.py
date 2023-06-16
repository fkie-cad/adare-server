from django.contrib.auth.models import User

from experiments.models import ExperimentRun, Status, OsInfo, Test, TestFunction, TestParameter, TestParameterEntries, \
    Tool, Result, Scenario, AbstractTest, Request, RequestStatus, Experiment
from helperfunctions.django_models import get_or_none, get_or_create

import logging
log = logging.getLogger(__name__)


def __create_experiment_from_data(data_dict: dict, user: User) -> (object, str):
    try:
        tests = data_dict['tests']
    except KeyError:
        return None, 'tests key not found'
    tests_objects = []
    for test in tests:
        test_obj = get_or_none(Test, uuid=test['uuid'])
        if test_obj is None:
            return None, f'test with uuid {test["uuid"]} not found'
        tests_objects.append(test_obj)
    experiment = get_or_none(Experiment, uuid=data_dict['uuid'])
    if experiment is not None:
        return experiment, 'experiment already exists'
    experiment = Experiment.objects.create(
        uuid=data_dict['uuid'],
        name=data_dict['name'],
        publisher=user,
    )
    for abstract_test in tests_objects:
        experiment.tests.add(abstract_test)
    experiment.save()
    return experiment, 'experiment created'


def __get_experiment_from_data(data_dict: dict) -> (object, str):
    try:
        experiment = get_or_none(Experiment, uuid=data_dict['uuid'])
    except KeyError:
        return None, f'experiment data has no uuid key'
    if experiment is None:
        return None, f'experiment with uuid {data_dict["uuid"]} not found'
    return experiment, 'experiment found'


def __get_request_status(status_name: str) -> RequestStatus:
    return get_or_none(RequestStatus, name=status_name)
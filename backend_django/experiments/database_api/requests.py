from django.contrib.auth.models import User
from django.utils.timezone import make_aware

from rest_framework.status import *

from datetime import datetime

from experiments.models import ExperimentRun, Status, OsInfo, Test, TestFunction, TestParameter, TestParameterEntries, \
    Tool, Result, Scenario, AbstractTest, Request, RequestStatus, Experiment
from experiments.database_api.helpers import __get_experiment_from_data, __get_request_status
from helperfunctions.django_models import get_or_none, get_or_create

import logging
log = logging.getLogger(__name__)


def create_request_experiment_creation(data_dict: dict, requestor: User):
    experiment_information = data_dict['experiment']
    experiment, msg = __get_experiment_from_data(data_dict=experiment_information)
    if not experiment:
        return msg, HTTP_400_BAD_REQUEST
    request_status = __get_request_status('not assigned')

    scenario_list = []
    for scenario_uuid in data_dict['scenario_uuids']:
        exp = get_or_none(Experiment, uuid=scenario_uuid)
        if not exp:
            msg = f'scenario with uuid {scenario_uuid} not found'
            log.error(msg)
        else:
            scenario_list.append(exp)

    experiment.scenario_runs.add(*scenario_list)
    experiment.save()

    request = Request.objects.create(
        requestor=requestor,
        last_changed=make_aware(datetime.now()),
        status=request_status,
        experiment=experiment,
    )
    request.save()
    log.info(f'created request {request.uuid} for experiment {experiment.uuid}')
    return f'request for experiment {experiment.uuid} got created successfully', HTTP_200_OK


def accept_request_experiment_creation(data_dict: dict, supervisor: User):
    request = get_or_none(Request, uuid=data_dict['request_uuid'])
    if not request:
        msg = f'request with uuid {data_dict["request_uuid"]} not found'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    request.status = __get_request_status('accepted')
    request.supervisor = supervisor
    request.experiment.publish_date = make_aware(datetime.now())
    request.experiment.published = True
    request.experiment.save()
    request.last_changed = make_aware(datetime.now())
    request.save()
    msg = f'request {request.uuid} got accepted by {supervisor.username}'
    log.info(msg)
    return msg, HTTP_200_OK


def decline_request_experiment_creation(data_dict: dict, supervisor: User):
    request = get_or_none(Request, uuid=data_dict['request_uuid'])
    if not request:
        msg = f'request with uuid {data_dict["request_uuid"]} not found'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    request.status = __get_request_status('declined')
    request.supervisor = supervisor
    request.last_changed = make_aware(datetime.now())
    request.save()
    msg = f'request {request.uuid} got declined by {supervisor.username}'
    log.info(msg)
    return msg, HTTP_200_OK


def assign_supervisor_to_request(data_dict: dict, user: User):
    request = get_or_none(Request, uuid=data_dict['request_uuid'])
    if not request:
        msg = f'request with uuid {data_dict["request_uuid"]} not found'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    assigned_supervisor = get_or_none(User, username=data_dict['supervisor_username'])
    if not assigned_supervisor:
        msg = f'user with username {data_dict["supervisor_username"]} not found'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    if assigned_supervisor.role != 'supervisor':
        msg = f'user with username {data_dict["supervisor_username"]} is not a supervisor'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    request.supervisor = assigned_supervisor
    request.supervisor_assigned_by = user
    request.last_changed = make_aware(datetime.now())
    request.save()
    msg = f'request {request.uuid} got assigned to {assigned_supervisor.username}'
    log.info(msg)
    return msg, HTTP_200_OK


def unassign_supervisor_from_request(data_dict: dict):
    request = get_or_none(Request, uuid=data_dict['request_uuid'])
    if not request:
        msg = f'request with uuid {data_dict["request_uuid"]} not found'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    if not request.supervisor:
        msg = f'request {request.uuid} has no supervisor assigned'
        log.error(msg)
        return msg, HTTP_400_BAD_REQUEST

    request.supervisor = None
    request.supervisor_assigned_by = None
    request.last_changed = make_aware(datetime.now())
    request.save()
    msg = f'request {request.uuid} got unassigned from supervisor'
    log.info(msg)
    return msg, HTTP_200_OK

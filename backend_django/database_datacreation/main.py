import string

import requests
import json
import uuid
import random
import urllib3
import datetime

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

URL = "http://127.0.0.1:8000/api/"
CSRF_URL = URL + "csrf/"
LOGIN_URL = URL + "user/login/"
SCENARIO_CREATE_URL = URL + "scenario/create/"
EXPERIMENT_CREATE_URL = URL + "experiment/create/"
REQUEST_EXPERIMENT_CREATE_URL = URL + "request/experiment/create/"
REQUEST_SCENARIO_CREATE_URL = URL + "request/scenario/create/"

SESSION = requests.Session()

TAGS = [
    'Windows',
    'Linux',
    'Explorer',
    'Chrome',
    'Firefox',
    'Edge',
    'Safari',
    'TrashBin',
    'RecycleBin',
    'Desktop',
    'ShimCache',
    'Prefetch',
    'Registry',
    'EventLog',
    'Memory',
    'File',
    'Process',
]

ABSTRACT_TESTS = [
    {
        "uuid": "d30aafb8-7dde-494e-a120-7aa9bbe46cac",
        "name": "deleted dir exists",
        "description": "tests whether the trash bin dir exists",
        "testfunction": {
            "name": "is_dir",
            "description": "tests whether a directory (dst) exists or not",
            "possible_parameters": [{
                "name": "dst",
                "dtype": "str"
            }]
        },
        "parameters": [
            {
                "parameter": {
                    "name": "dst",
                    "dtype": "str"
                },
                "value": "C:/Users/.randomdir"
            }
        ]
    },
    {
        "uuid": "e86bd0a4-7034-4f3f-bc3e-a59b52162538",
        "name": "deleted file exists",
        "description": "tests whether the trash bin file exists",
        "testfunction": {
            "name": "is_file",
            "description": "tests whether a file (dst) exists or not",
            "possible_parameters": [{
                "name": "dst",
                "dtype": "str"
            }]
        },
        "parameters": [
            {
                "parameter": {
                    "name": "dst",
                    "dtype": "str"
                },
                "value": "C:/Users/.randomfile"
            }
        ]
    },
]

OS_INFO_LIST = [
    {
        'os': 'Windows',
        'distribution': 'Windows 10',
        'version': '10.0.19042',
        'architecture': 'x64',
        'language': 'English',
    },
    {
        'os': 'Windows',
        'distribution': 'Windows 7',
        'version': '6.1.7601',
        'architecture': 'x64',
        'language': 'English',
    },
    {
        'os': 'Windows',
        'distribution': 'Windows 8.1',
        'version': '6.3.9600',
        'architecture': 'x64',
        'language': 'English',
    },
    {
        'os': 'Linux',
        'distribution': 'Ubuntu',
        'version': '20.04',
        'architecture': 'x64',
        'language': 'English',
    },
]

USER_LIST = [
    {
        "username": "admin",
        "password": "admin",
        "groups": ["admin"],
    },
    {
        "username": "testuser1_none",
        "password": "test",
        "groups": [],
    },
    {
        "username": "testuser2_supervisor",
        "password": "test",
        "groups": ["supervisor"],
    },
    {
        "username": "testuser6_supervisor",
        "password": "test",
        "groups": ["supervisor"],
    },
]


def convert_abstract_tests_to_tests(abstract_tests: list) -> list:
    """
    Converts abstract tests to tests
    """
    tests = []
    for abstract_test in abstract_tests:
        test = {
            "uuid": str(uuid.uuid4()),
            "abstracttest": abstract_test['name'],
            "result": {
                "status": {
                    "name": "success"
                },
                "details": ""
            }
        }
        tests.append(test)
    return tests



def __generate_random_string(length: int) -> str:
    """
    Generates a random string with the given length
    """
    return ''.join(random.choice(string.ascii_letters+string.digits) for _ in range(length))


def __choose_random_tags(length: int, tags_list=None) -> list:
    """
    Chooses a fixed amount of tags from the given list
    """
    if tags_list is None:
        tags_list = TAGS
    return random.sample(tags_list, length)


def __random_osinfo() -> dict:
    """
    Generates random os information
    """
    return random.choice(OS_INFO_LIST)


def __generate_random_experiment_data(scenario_uuids: list) -> dict:
    """
    Generates random experiment data
    """
    num_tags = random.randint(1, len(TAGS))
    # choose random scenario uuid
    scenario_uuid = random.choice(scenario_uuids)
    experiment_uuid = str(uuid.uuid4())
    experiment_name = 'Test Experiment ' + __generate_random_string(8)
    experiment_data = {
        'uuid': experiment_uuid,
        'scenario_uuid': scenario_uuid,
        'name': experiment_name,
        'description': f'This is a test experiment {experiment_name}',
        'tags': [{
            'name': tag
        } for tag in __choose_random_tags(num_tags)],
        'os_info': __random_osinfo(),
        'abstract_tests': ABSTRACT_TESTS,
    }
    return experiment_data


def __generate_random_scenario_data() -> dict:
    custom_name = 'Test Scenario ' + __generate_random_string(8)
    num_tags = random.randint(1, len(TAGS))
    custom_uuid = str(uuid.uuid4())
    scenario_data = {
        'uuid': custom_uuid,
        'name': custom_name,
        'experiments_uuids': [],
        'description': f'This is the test scenario {custom_name}',
        'tags': [{
            'name': tag
        } for tag in __choose_random_tags(num_tags)]
    }
    return scenario_data


def csrf():
    """
    Get the csrf token from API and add to the session
    """
    response = SESSION.get(CSRF_URL)
    response.raise_for_status()
    csrf = response.cookies['csrftoken']
    SESSION.headers.update({'X-CSRFToken': csrf})
    log.info(f'CSRF token {csrf} received')
    return csrf


def login(user, password) -> str:
    """
    Logs in the user and returns the token
    """
    csrf()
    response = SESSION.post(LOGIN_URL, json={"username": user, "password": password})
    response.raise_for_status()
    SESSION.headers.update({'Authorization': 'Token ' + response.json()["token"]})
    log.info(f'User {user} logged in')
    return response.json()["token"]


def add_scenario(num=1):
    scenario_uuids = []
    for i in range(num):
        # choose random user in group supervisor
        # user = random.choice([user for user in USER_LIST if 'supervisor' in user['groups']])
        # login(user['username'], user['password'])

        scenario_data = __generate_random_scenario_data()
        scenario_uuids.append(scenario_data['uuid'])
        response = SESSION.post(SCENARIO_CREATE_URL, json=scenario_data)
        response.raise_for_status()
        log.info(f'Scenario {scenario_data["name"]} ({i+1}/{num}) created')
    return scenario_uuids


def add_experiment(scenario_uuids: list, num=1):
    experiment_uuids = []
    for i in range(num):
        experiment_data = __generate_random_experiment_data(scenario_uuids)

        experiment_uuids.append(experiment_data['uuid'])
        form_data = {
            'metadata': json.dumps(experiment_data),
            'testset_file': ("testset_file.yml", open('pseudo_testset_file.yml').read()),
            'action_file': ("action_file.py", open('pseudo_action_file.py').read()),
        }

        body, content_type = urllib3.encode_multipart_formdata(form_data)

        response = SESSION.post(EXPERIMENT_CREATE_URL, data=body, headers={'Content-Type': content_type})
        response.raise_for_status()
        log.info(f'Experiment {experiment_data["name"]} ({i+1}/{num}) created')
    return experiment_uuids


def add_experiment_request(scenario_uuids, num=1):
    experiment_uuids = []
    request_uuids = []
    for i in range(num):
        experiment_data = __generate_random_experiment_data(scenario_uuids)
        experiment_uuids.append(experiment_data['uuid'])

        request_uuid = str(uuid.uuid4())
        request_data = {
            "title": f"REQ for Experiment {experiment_data['name']}",
            "uuid": request_uuid,
            "description": "This is a test request",
            "experiment": experiment_data,
        }
        request_uuids.append(request_uuid)

        form_data = {
            'metadata': json.dumps(request_data),
            'testset_file': ("testset_file.yml", open('pseudo_testset_file.yml').read()),
            'action_file': ("action_file.py", open('pseudo_action_file.py').read()),
        }

        body, content_type = urllib3.encode_multipart_formdata(form_data)

        response = SESSION.post(REQUEST_EXPERIMENT_CREATE_URL, data=body, headers={'Content-Type': content_type})
        response.raise_for_status()
        log.info(f'Request {request_data["uuid"]} created')

    return request_uuids, experiment_uuids


def add_scenario_request(num=1):
    request_uuids = []
    scenario_uuids = []

    for i in range(num):
        request_uuid = str(uuid.uuid4())
        scenario = __generate_random_scenario_data()
        request_data = {
            "title": f"REQ for Scenario {scenario['name']}",
            "uuid": request_uuid,
            "description": "This is a test request for Scenario",
            "scenario": scenario,
        }
        request_uuids.append(request_uuid)
        scenario_uuids.append(scenario['uuid'])

        form_data = {
            'metadata': json.dumps(request_data),
            'testset_file': ("testset_file.yml", open('pseudo_testset_file.yml').read()),
            'action_file': ("action_file.py", open('pseudo_action_file.py').read()),
        }

        body, content_type = urllib3.encode_multipart_formdata(form_data)
        response = SESSION.post(REQUEST_SCENARIO_CREATE_URL, data=body, headers={'Content-Type': content_type})
        response.raise_for_status()
        log.info(f'Request {request_data["uuid"]} created')

    return request_uuids, scenario_uuids


def add_experiment_run(experiment_uuid: str, num=5, failed_ratio=0.2):
    experiment_runs_uuids = []
    for i in range(num):
        # choose random status (failed or success) with a given ratio
        status = random.choices(['success', 'failed'], weights=[1-failed_ratio, failed_ratio])[0]
        custom_uuid = str(uuid.uuid4())

        # choose random start and end timestamp in the last 10 days (the difference between start and end is at most 5 minutes)
        start_timestamp = datetime.datetime.now() - datetime.timedelta(days=10)
        end_timestamp = start_timestamp + datetime.timedelta(minutes=random.randint(0, 5))

        experiment_run_data = {
            "uuid": custom_uuid,
            "experiment_uuid": experiment_uuid,
            "timestamp_start": start_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "timestamp_end": start_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "status": {
                "name": status
            },
            "tests": [{
                "uuid": "ed1ef23d-bcbb-44b1-8a0c-7f54a960f8ce",
                "abstracttest": "deleted file exists",
                "result": {
                    "status": {
                        "name": "success"
                    },
                    "details": ""
                }
            }]
        }

        experiment_runs_uuids.append(custom_uuid)


if __name__ == "__main__":
    login("testuser2_supervisor", "test")
    uuids = add_scenario(3)
    add_experiment_request(uuids, 3)
    add_scenario_request(3)


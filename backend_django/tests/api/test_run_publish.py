import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from experiments.models import ExperimentRun, Status, CommandEvent, generate_ulid
from tests.factories import (
    ExperimentFactory,
    ExperimentRunFactory,
    EnvironmentFactory,
    CommandEventFactory,
    AbstractTestFactory,
    GiteaUserFactory,
)


def _build_metadata(*, run_ulid, experiment, environment, status_id, result_status_id, events=None):
    """Helper to build the metadata JSON dict for the publish endpoint."""
    return {
        'ulid': run_ulid,
        'experiment_ulid': experiment.ulid,
        'environment_ulid': environment.ulid,
        'status': status_id,
        'result_status': result_status_id,
        'timestamp_start': '2024-01-15T10:00:00Z',
        'timestamp_end': '2024-01-15T10:01:00Z',
        'events': events or [],
    }


def _make_command_event(status_id):
    return {
        'ulid': generate_ulid(),
        'category': 'command',
        'status': status_id,
        'error': '',
        'group_id': 1,
        'timestamp': '2024-01-15T10:00:10Z',
        'name': 'install-packages',
        'command': 'apt install vim',
        'returncode': 0,
        'stdout': 'done',
    }


def _make_test_event(status_id, result_status_id, abstract_test_ulid):
    return {
        'ulid': generate_ulid(),
        'category': 'test',
        'status': status_id,
        'error': '',
        'group_id': 2,
        'timestamp': '2024-01-15T10:00:20Z',
        'result': {
            'status': result_status_id,
            'details': 'file found',
        },
        'abstract_test_ulid': abstract_test_ulid,
    }


def _make_error_event(status_id):
    return {
        'ulid': generate_ulid(),
        'category': 'error',
        'status': status_id,
        'error': '',
        'group_id': 3,
        'timestamp': '2024-01-15T10:00:30Z',
        'error_name': 'TimeoutError',
        'error_msg': 'Command timed out after 60s',
    }


def _make_gui_find_event(status_id):
    return {
        'ulid': generate_ulid(),
        'category': 'gui:find',
        'status': status_id,
        'error': '',
        'group_id': 4,
        'timestamp': '2024-01-15T10:00:40Z',
        'text': True,
        'objective': 'Find OK button',
        'success': 1,
        'positions': '',
    }


def _make_gui_click_event(status_id):
    return {
        'ulid': generate_ulid(),
        'category': 'gui:click',
        'status': status_id,
        'error': '',
        'group_id': 5,
        'timestamp': '2024-01-15T10:00:41Z',
        'clicktype': 'single',
        'modifiers': '',
        'target': 'button',
    }


def _make_gui_keypress_event(status_id):
    return {
        'ulid': generate_ulid(),
        'category': 'gui:keypress',
        'status': status_id,
        'error': '',
        'group_id': 6,
        'timestamp': '2024-01-15T10:00:42Z',
        'keys': 'enter',
    }


def _make_gui_idle_event(status_id):
    return {
        'ulid': generate_ulid(),
        'category': 'gui:idle',
        'status': status_id,
        'error': '',
        'group_id': 7,
        'timestamp': '2024-01-15T10:00:43Z',
        'seconds': 5,
    }


def _log_files():
    """Return dict of SimpleUploadedFile objects for the three required log files."""
    return {
        'adarevm_log': SimpleUploadedFile('adarevm.log', b'adarevm log content'),
        'installations_log': SimpleUploadedFile('installations.log', b'installations log content'),
        'packagedump_log': SimpleUploadedFile('packagedump.log', b'packagedump log content'),
    }


@pytest.fixture
def publish_prerequisites(db, gitea_user):
    """Create the experiment, environment, and statuses needed for publishing a run."""
    env = EnvironmentFactory(published_by=gitea_user)
    abstract_test = AbstractTestFactory()
    experiment = ExperimentFactory(
        published_by=gitea_user,
        environments=[env],
        abstract_tests=[abstract_test],
    )
    finished = Status.objects.get(name='finished')
    success = Status.objects.get(name='success')
    return {
        'experiment': experiment,
        'environment': env,
        'abstract_test': abstract_test,
        'finished': finished,
        'success': success,
        'gitea_user': gitea_user,
    }


@pytest.mark.django_db
class TestPublishWithEvents:

    def test_publish_with_command_events(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        events = [
            _make_command_event(p['finished'].id),
            _make_command_event(p['finished'].id),
        ]
        # Give the second event a distinct group_id
        events[1]['group_id'] = 10

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        assert ExperimentRun.objects.filter(ulid=metadata['ulid']).exists()

    def test_publish_with_test_events(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        events = [
            _make_test_event(p['finished'].id, p['success'].id, p['abstract_test'].ulid),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        assert ExperimentRun.objects.filter(ulid=metadata['ulid']).exists()

    def test_publish_with_all_event_types(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        events = [
            _make_command_event(p['finished'].id),
            _make_test_event(p['finished'].id, p['success'].id, p['abstract_test'].ulid),
            _make_error_event(p['finished'].id),
            _make_gui_find_event(p['finished'].id),
            _make_gui_click_event(p['finished'].id),
            _make_gui_keypress_event(p['finished'].id),
            _make_gui_idle_event(p['finished'].id),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        run = ExperimentRun.objects.get(ulid=metadata['ulid'])
        assert run.command_events.count() == 1
        assert run.test_events.count() == 1
        assert run.error_events.count() == 1
        assert run.gui_find_events.count() == 1
        assert run.gui_click_events.count() == 1
        assert run.gui_keypress_events.count() == 1
        assert run.gui_idle_events.count() == 1

    def test_publish_with_log_files(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        run = ExperimentRun.objects.get(ulid=metadata['ulid'])
        assert run.adarevm_logfile
        assert run.installations_logfile
        assert run.packagedump_logfile


@pytest.mark.django_db
class TestPublishValidation:

    def test_duplicate_run_ulid_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        existing_run = ExperimentRunFactory(
            experiment=p['experiment'],
            environment=p['environment'],
            published_by=p['gitea_user'],
        )

        metadata = _build_metadata(
            run_ulid=existing_run.ulid,
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400

    def test_nonexistent_experiment_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        fake_exp_ulid = generate_ulid()

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=[],
        )
        metadata['experiment_ulid'] = fake_exp_ulid

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400

    def test_nonexistent_environment_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        fake_env_ulid = generate_ulid()

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=[],
        )
        metadata['environment_ulid'] = fake_env_ulid

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400

    def test_duplicate_event_ulid_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites

        # Create an existing event with a known ulid
        existing_run = ExperimentRunFactory(
            experiment=p['experiment'],
            environment=p['environment'],
            published_by=p['gitea_user'],
        )
        existing_event = CommandEventFactory(run=existing_run, group_id=99)

        # Build a new run that re-uses the existing event ulid
        cmd_event = _make_command_event(p['finished'].id)
        cmd_event['ulid'] = existing_event.ulid

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=[cmd_event],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestPublishAuthentication:

    def test_requires_authentication(self, api_client, publish_prerequisites):
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_id=p['finished'].id,
            result_status_id=p['success'].id,
            events=[],
        )

        response = api_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 401

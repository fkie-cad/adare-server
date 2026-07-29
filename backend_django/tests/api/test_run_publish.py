import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from experiments.models import ExperimentRun, Status, ActionEvent, TestEvent, ErrorEvent, Result, generate_ulid
from tests.factories import (
    ExperimentFactory,
    ExperimentRunFactory,
    EnvironmentFactory,
    ActionEventFactory,
    AbstractTestFactory,
    GiteaUserFactory,
)


def _build_metadata(*, run_ulid, experiment, environment, status_name, result_status_name, events=None, content_hash=''):
    """Helper to build the metadata JSON dict for the publish endpoint."""
    return {
        'ulid': run_ulid,
        'experiment_ulid': experiment.ulid,
        'environment_ulid': environment.ulid,
        'status': status_name,
        'result_status': result_status_name,
        'timestamp_start': '2024-01-15T10:00:00Z',
        'timestamp_end': '2024-01-15T10:01:00Z',
        'events': events or [],
        'content_hash': content_hash,
    }


def _make_action_event(status_name, *, category='command', success=None,
                       execution_time=None, event_type_specific=''):
    d = {
        'ulid': generate_ulid(),
        'category': category,
        'status': status_name,
        'error': '',
        'event_group_id': '1',
        'timestamp': '2024-01-15T10:00:10Z',
        'action_type': 'command',
        'action_id': 'install-packages',
        'action_data': '{"command": "apt install vim", "returncode": 0, "stdout": "done"}',
    }
    if success is not None:
        d['success'] = success
    if execution_time is not None:
        d['execution_time'] = execution_time
    if event_type_specific:
        d['event_type_specific'] = event_type_specific
    return d


def _make_test_event(status_name, result_status_name, abstract_test_ulid, *,
                     success=None, execution_time=None, event_type_specific=''):
    d = {
        'ulid': generate_ulid(),
        'category': 'test',
        'status': status_name,
        'error': '',
        'event_group_id': '2',
        'timestamp': '2024-01-15T10:00:20Z',
        'result': {
            'status': result_status_name,
            'details': 'file found',
        },
        'abstract_test_ulid': abstract_test_ulid,
    }
    if success is not None:
        d['success'] = success
    if execution_time is not None:
        d['execution_time'] = execution_time
    if event_type_specific:
        d['event_type_specific'] = event_type_specific
    return d


def _make_error_event(status_name, *, success=None, execution_time=None,
                      event_type_specific=''):
    d = {
        'ulid': generate_ulid(),
        'category': 'error',
        'status': status_name,
        'error': '',
        'event_group_id': '3',
        'timestamp': '2024-01-15T10:00:30Z',
        'error_name': 'TimeoutError',
        'error_msg': 'Command timed out after 60s',
    }
    if success is not None:
        d['success'] = success
    if execution_time is not None:
        d['execution_time'] = execution_time
    if event_type_specific:
        d['event_type_specific'] = event_type_specific
    return d


def _log_files():
    """Return dict of SimpleUploadedFile objects for log files."""
    return {
        'adarevm_log': SimpleUploadedFile('adarevm.log', b'adarevm log content'),
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
    return {
        'experiment': experiment,
        'environment': env,
        'abstract_test': abstract_test,
        'gitea_user': gitea_user,
    }


@pytest.mark.django_db
class TestPublishWithEvents:

    def test_publish_with_action_events(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        events = [
            _make_action_event('finished'),
            _make_action_event('finished'),
        ]
        events[1]['event_group_id'] = '10'

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
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
            _make_test_event('finished', 'success', p['abstract_test'].ulid),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
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
            _make_action_event('finished'),
            _make_test_event('finished', 'success', p['abstract_test'].ulid),
            _make_error_event('finished'),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        run = ExperimentRun.objects.get(ulid=metadata['ulid'])
        assert run.action_events.count() == 1
        assert run.test_events.count() == 1
        assert run.error_events.count() == 1

    def test_publish_with_log_files(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
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

    def test_idempotent_reupload(self, authenticated_client, publish_prerequisites):
        """Re-uploading the same run_ulid should return 200 instead of error."""
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
            status_name='finished',
            result_status_name='success',
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 200

    def test_content_hash_dedup(self, authenticated_client, publish_prerequisites):
        """Different ULID but same content_hash should return 409."""
        p = publish_prerequisites
        existing_run = ExperimentRunFactory(
            experiment=p['experiment'],
            environment=p['environment'],
            published_by=p['gitea_user'],
            content_hash='abc123deadbeef',
        )

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
            content_hash='abc123deadbeef',
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 409
        assert response.data['error'] == 'content_duplicate'

    def test_publish_action_event_with_all_base_fields(self, authenticated_client, publish_prerequisites):
        """success, execution_time, event_type_specific are stored in the DB."""
        p = publish_prerequisites
        events = [
            _make_action_event('finished', success=True, execution_time=1500,
                               event_type_specific='CLICK_COMPLETE'),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        action = ActionEvent.objects.get(ulid=events[0]['ulid'])
        assert action.success is True
        assert action.execution_time == 1500
        assert action.event_type_specific == 'CLICK_COMPLETE'

    def test_publish_action_event_category_action(self, authenticated_client, publish_prerequisites):
        """category='action' maps to ActionEvent (not just 'command')."""
        p = publish_prerequisites
        events = [
            _make_action_event('finished', category='action'),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        action = ActionEvent.objects.get(ulid=events[0]['ulid'])
        assert action.category == 'action'

    def test_publish_test_event_creates_result(self, authenticated_client, publish_prerequisites):
        """TestEvent creates a Result object with correct status and details."""
        p = publish_prerequisites
        events = [
            _make_test_event('finished', 'success', p['abstract_test'].ulid),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        test_event = TestEvent.objects.get(ulid=events[0]['ulid'])
        assert test_event.result is not None
        assert test_event.result.status.name == 'success'
        assert test_event.result.details == 'file found'

    def test_publish_multiple_test_events(self, authenticated_client, publish_prerequisites):
        """Two TestEvents with different AbstractTests in one run."""
        p = publish_prerequisites
        abstract_test_2 = AbstractTestFactory()
        p['experiment'].abstract_tests.add(abstract_test_2)

        events = [
            _make_test_event('finished', 'success', p['abstract_test'].ulid),
            _make_test_event('finished', 'success', abstract_test_2.ulid),
        ]
        events[1]['event_group_id'] = '20'

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        run = ExperimentRun.objects.get(ulid=metadata['ulid'])
        assert run.test_events.count() == 2

    def test_publish_events_without_status_key(self, authenticated_client, publish_prerequisites):
        """Events with no 'status' field auto-default to 'finished'."""
        p = publish_prerequisites
        events = [_make_action_event('finished')]
        del events[0]['status']

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        action = ActionEvent.objects.get(ulid=events[0]['ulid'])
        assert action.status.name == 'finished'

    def test_publish_events_without_event_group_id(self, authenticated_client, publish_prerequisites):
        """Events with empty event_group_id get auto-assigned sequential IDs."""
        p = publish_prerequisites
        events = [
            _make_action_event('finished'),
            _make_action_event('finished'),
        ]
        events[0]['event_group_id'] = ''
        events[1]['event_group_id'] = ''

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        e0 = ActionEvent.objects.get(ulid=events[0]['ulid'])
        e1 = ActionEvent.objects.get(ulid=events[1]['ulid'])
        assert e0.event_group_id == '0'
        assert e1.event_group_id == '1'

    def test_publish_run_without_any_log_files(self, authenticated_client, publish_prerequisites):
        """POST with only metadata, no file attachments at all."""
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata)},
            format='multipart',
        )

        assert response.status_code == 201
        run = ExperimentRun.objects.get(ulid=metadata['ulid'])
        assert not run.adarevm_logfile

    def test_publish_with_success_false_and_none(self, authenticated_client, publish_prerequisites):
        """Events with success=False and success=None roundtrip correctly."""
        p = publish_prerequisites
        events = [
            _make_action_event('finished', success=False),
            _make_action_event('finished', success=None),
        ]
        events[0]['event_group_id'] = '10'
        events[1]['event_group_id'] = '11'

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        e_false = ActionEvent.objects.get(ulid=events[0]['ulid'])
        e_none = ActionEvent.objects.get(ulid=events[1]['ulid'])
        assert e_false.success is False
        assert e_none.success is None


@pytest.mark.django_db
class TestPublishValidation:

    def test_nonexistent_experiment_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        fake_exp_ulid = generate_ulid()

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
        )
        metadata['experiment_ulid'] = fake_exp_ulid

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400
        assert response.data['error'] == 'experiment_not_found'

    def test_nonexistent_environment_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        fake_env_ulid = generate_ulid()

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
        )
        metadata['environment_ulid'] = fake_env_ulid

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400
        assert response.data['error'] == 'environment_not_found'

    def test_duplicate_event_ulid_rejected(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites

        # Create an existing event with a known ulid
        existing_run = ExperimentRunFactory(
            experiment=p['experiment'],
            environment=p['environment'],
            published_by=p['gitea_user'],
        )
        existing_event = ActionEventFactory(run=existing_run, event_group_id='99')

        # Build a new run that re-uses the existing event ulid
        action_event = _make_action_event('finished')
        action_event['ulid'] = existing_event.ulid

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[action_event],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400

    def test_mid_loop_failure_rolls_back_entire_run(self, authenticated_client, publish_prerequisites):
        """A failure on event #2 of 3 must not leave the run or event #1 committed.

        Regression test: _process_events used to return an error Response
        instead of raising, so events already saved before the failing one
        (plus the ExperimentRun row and its content_hash) stayed committed
        even though the client received a 400 for the whole request. A retry
        would then hit the idempotent short-circuit and report success
        without ever ingesting the remaining events.
        """
        p = publish_prerequisites

        existing_run = ExperimentRunFactory(
            experiment=p['experiment'],
            environment=p['environment'],
            published_by=p['gitea_user'],
        )
        existing_event = ActionEventFactory(run=existing_run, event_group_id='99')

        good_event = _make_action_event('finished')
        good_event['event_group_id'] = '1'
        duplicate_event = _make_action_event('finished')
        duplicate_event['ulid'] = existing_event.ulid  # triggers failure
        duplicate_event['event_group_id'] = '2'
        another_event = _make_action_event('finished')
        another_event['event_group_id'] = '3'

        run_ulid = generate_ulid()
        metadata = _build_metadata(
            run_ulid=run_ulid,
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[good_event, duplicate_event, another_event],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400
        assert not ExperimentRun.objects.filter(ulid=run_ulid).exists()
        assert not ActionEvent.objects.filter(ulid=good_event['ulid']).exists()
        assert not ActionEvent.objects.filter(ulid=another_event['ulid']).exists()

        # A subsequent retry with the fixed payload should fully succeed
        # (proves the failed attempt didn't leave the ulid in a half-claimed
        # state that would trip the idempotent/dup-event checks).
        fixed_duplicate_event = _make_action_event('finished')
        fixed_duplicate_event['event_group_id'] = '2'
        retry_metadata = _build_metadata(
            run_ulid=run_ulid,
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[good_event, fixed_duplicate_event, another_event],
        )
        retry_response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(retry_metadata), **_log_files()},
            format='multipart',
        )
        assert retry_response.status_code == 201
        run = ExperimentRun.objects.get(ulid=run_ulid)
        assert run.action_events.count() == 3

    def test_unpublished_experiment_rejected(self, authenticated_client, publish_prerequisites):
        """Experiment with published=False returns 400 with experiment_not_published."""
        p = publish_prerequisites
        p['experiment'].published = False
        p['experiment'].save()

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400
        assert response.data['error'] == 'experiment_not_published'

    def test_invalid_status_name_rejected(self, authenticated_client, publish_prerequisites):
        """status='bogus' returns 400 with validation_error."""
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='bogus',
            result_status_name='success',
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400
        assert response.data['error'] == 'validation_error'

    def test_invalid_result_status_name_rejected(self, authenticated_client, publish_prerequisites):
        """result_status='bogus' returns 400 with validation_error."""
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='bogus',
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 400
        assert response.data['error'] == 'validation_error'


@pytest.mark.django_db
class TestPublishAuthentication:

    def test_requires_authentication(self, api_client, publish_prerequisites):
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
        )

        response = api_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestRealisticClientPayload:
    """Contract test mirroring exact client serialize_run()/serialize_event() output."""

    def test_realistic_payload_roundtrip(self, authenticated_client, publish_prerequisites):
        p = publish_prerequisites
        import hashlib
        run_ulid = generate_ulid()
        action_ulid = generate_ulid()
        test_ulid = generate_ulid()
        error_ulid = generate_ulid()
        content_hash = hashlib.sha256(b'realistic-payload-test').hexdigest()

        # Client timestamps use '%Y-%m-%dT%H:%M:%S.%f' (no 'Z', with microseconds)
        events = [
            {
                'ulid': action_ulid,
                'category': 'action',
                'action_type': 'click',
                'action_id': 'btn-submit',
                'action_data': '{"target": "#submit", "x": 100, "y": 200}',
                'error': '',
                'event_group_id': '',
                'timestamp': '2024-01-15T10:00:10.123456',
                'success': True,
                'execution_time': 350,
                'event_type_specific': 'CLICK',
            },
            {
                'ulid': test_ulid,
                'category': 'test',
                'error': '',
                'event_group_id': '',
                'timestamp': '2024-01-15T10:00:20.654321',
                'success': True,
                'execution_time': 500,
                'event_type_specific': '',
                'result': {
                    'status': 'success',
                    'details': 'file /etc/hosts exists',
                },
                'abstract_test_ulid': p['abstract_test'].ulid,
            },
            {
                'ulid': error_ulid,
                'category': 'error',
                'error': '',
                'event_group_id': '',
                'timestamp': '2024-01-15T10:00:30.000000',
                'error_name': 'Error',
                'error_msg': 'Connection refused on port 8080',
            },
        ]
        # Client never sends 'status' on events — server defaults to 'finished'

        metadata = {
            'ulid': run_ulid,
            'experiment_ulid': p['experiment'].ulid,
            'environment_ulid': p['environment'].ulid,
            'status': 'finished',
            'result_status': 'success',
            'timestamp_start': '2024-01-15T10:00:00.000000',
            'timestamp_end': '2024-01-15T10:01:00.000000',
            'events': events,
            'content_hash': content_hash,
        }

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201

        # Verify DB state
        run = ExperimentRun.objects.get(ulid=run_ulid)
        assert run.status.name == 'finished'
        assert run.result_status.name == 'success'
        assert run.content_hash == content_hash

        # Verify action event
        action = ActionEvent.objects.get(ulid=action_ulid)
        assert action.category == 'action'
        assert action.action_type == 'click'
        assert action.action_data == '{"target": "#submit", "x": 100, "y": 200}'
        assert action.success is True
        assert action.execution_time == 350
        assert action.event_type_specific == 'CLICK'
        assert action.status.name == 'finished'  # auto-defaulted

        # Verify test event and result
        test_event = TestEvent.objects.get(ulid=test_ulid)
        assert test_event.result is not None
        assert test_event.result.status.name == 'success'
        assert test_event.result.details == 'file /etc/hosts exists'
        assert test_event.abstracttest.ulid == p['abstract_test'].ulid
        assert test_event.success is True
        assert test_event.execution_time == 500

        # Verify error event
        error_event = ErrorEvent.objects.get(ulid=error_ulid)
        assert error_event.error_name == 'Error'
        assert error_event.error_msg == 'Connection refused on port 8080'
        assert error_event.status.name == 'finished'  # auto-defaulted

        # Verify auto-assigned event_group_ids (all were empty)
        assert action.event_group_id == '0'
        assert test_event.event_group_id == '1'
        assert error_event.event_group_id == '2'

        # GET detail and verify events roundtrip
        detail_response = authenticated_client.get(f'/api/run/run_{run_ulid}/')
        assert detail_response.status_code == 200
        detail_events = detail_response.data['events']
        assert len(detail_events) == 3

        # Find each event type in the response
        event_by_ulid = {e['ulid']: e for e in detail_events}
        assert action_ulid in event_by_ulid
        assert test_ulid in event_by_ulid
        assert error_ulid in event_by_ulid

        # Verify action event fields in API response
        api_action = event_by_ulid[action_ulid]
        assert api_action['category'] == 'action'
        assert api_action['action_type'] == 'click'
        assert api_action['success'] is True
        assert api_action['execution_time'] == 350
        assert api_action['event_type_specific'] == 'CLICK'
        assert api_action['status']['name'] == 'finished'

        # Verify test event fields in API response
        api_test = event_by_ulid[test_ulid]
        assert api_test['result']['status']['name'] == 'success'
        assert api_test['result']['details'] == 'file /etc/hosts exists'


@pytest.mark.django_db
class TestPublishResponseValidation:

    def test_publish_response_contains_run_fields(self, authenticated_client, publish_prerequisites):
        """201 response has all expected run fields."""
        p = publish_prerequisites

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=[],
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )

        assert response.status_code == 201
        data = response.data
        assert 'ulid' in data
        assert 'status' in data
        assert 'result_status' in data
        assert 'experiment' in data
        assert 'environment' in data
        assert 'timestamp_start' in data
        assert 'timestamp_end' in data

    def test_detail_response_event_fields(self, authenticated_client, publish_prerequisites):
        """GET detail after publish — each event has all base + type-specific fields."""
        p = publish_prerequisites
        events = [
            _make_action_event('finished', success=True, execution_time=100),
            _make_test_event('finished', 'success', p['abstract_test'].ulid,
                             success=True, execution_time=200),
            _make_error_event('finished'),
        ]

        metadata = _build_metadata(
            run_ulid=generate_ulid(),
            experiment=p['experiment'],
            environment=p['environment'],
            status_name='finished',
            result_status_name='success',
            events=events,
        )

        response = authenticated_client.post(
            '/api/run/publish/',
            {'metadata': json.dumps(metadata), **_log_files()},
            format='multipart',
        )
        assert response.status_code == 201

        detail = authenticated_client.get(f'/api/run/run_{metadata["ulid"]}/')
        assert detail.status_code == 200

        base_fields = {'ulid', 'category', 'status', 'success', 'event_group_id',
                       'event_type_specific', 'execution_time', 'timestamp'}

        for event in detail.data['events']:
            assert base_fields.issubset(event.keys()), \
                f"Event {event.get('ulid')} missing base fields: {base_fields - event.keys()}"

            if event['category'] in ('command', 'action'):
                assert 'action_type' in event
                assert 'action_id' in event
                assert 'action_data' in event
            elif event['category'] == 'test':
                assert 'result' in event
                assert 'abstracttest' in event
            elif event['category'] == 'error':
                assert 'error_name' in event
                assert 'error_msg' in event

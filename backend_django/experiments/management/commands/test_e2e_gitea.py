"""
E2E test management command — exercises the full Gitea-driven lifecycle:
submit → PR → webhook → merge → publish → run publish → verify → cleanup.

Usage:
    python manage.py test_e2e_gitea
    python manage.py test_e2e_gitea --skip-cleanup --verbose
"""
import json
import time
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APIClient

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'tests' / 'fixtures'


class Phase:
    """Tracks pass/fail for a named phase."""

    def __init__(self, name, stdout, verbose=False):
        self.name = name
        self.stdout = stdout
        self.verbose = verbose
        self.assertions = []

    def check(self, condition, description):
        passed = bool(condition)
        self.assertions.append((description, passed))
        mark = '\033[92m✓\033[0m' if passed else '\033[91m✗\033[0m'
        self.stdout.write(f'  {mark} {description}')
        return passed

    @property
    def passed(self):
        return all(ok for _, ok in self.assertions)

    @property
    def summary(self):
        total = len(self.assertions)
        ok = sum(1 for _, p in self.assertions if p)
        return f'{self.name}: {ok}/{total} passed'


class Command(BaseCommand):
    help = 'Run E2E tests against Gitea (requires running Gitea and Celery)'

    def add_arguments(self, parser):
        parser.add_argument('--skip-cleanup', action='store_true',
                            help='Do not reset repo after tests (for debugging)')
        parser.add_argument('--test-repo', default='adareTEST',
                            help='Gitea repo name (default: adareTEST)')
        parser.add_argument('--repo-owner', default=None,
                            help='Gitea repo owner (default: from settings)')
        parser.add_argument('--verbose', action='store_true',
                            help='Show detailed progress')
        parser.add_argument('--interactive', action='store_true',
                            help='Pause after each phase for manual GUI inspection')

    def _pause(self, phase_name):
        """Pause for manual inspection. Returns True to continue, False to stop."""
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            f'  ⏸  Paused after {phase_name}. Check the GUI now.'
        ))
        self.stdout.write(f'      Frontend: http://localhost:9000')
        self.stdout.write(f'      API:      http://localhost:8001/api/')
        self.stdout.write('')
        try:
            answer = input('  Press Enter to continue, "q" to stop (keeps state), "r" to revert & stop: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = 'q'
        if answer == 'q':
            self.stdout.write(self.style.WARNING('  Stopping. State preserved for inspection.'))
            return 'stop'
        elif answer == 'r':
            return 'revert'
        return 'continue'

    def handle(self, *args, **options):
        start_time = time.time()
        skip_cleanup = options['skip_cleanup']
        test_repo = options['test_repo']
        repo_owner = options.get('repo_owner') or settings.GITEA_EXPERIMENTS_REPO_OWNER
        verbose = options['verbose']
        interactive = options['interactive']

        phases = []

        # ── Phase 0: Setup ──────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 0: Setup ═══'))

        # Save original settings
        original_repo = settings.GITEA_EXPERIMENTS_REPO
        original_repo_owner = settings.GITEA_EXPERIMENTS_REPO_OWNER
        original_celery_eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)

        # Swap to test config
        settings.GITEA_EXPERIMENTS_REPO = test_repo
        settings.GITEA_EXPERIMENTS_REPO_OWNER = repo_owner
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True
        settings.ALLOWED_HOSTS = ['*']

        # Initialize Gitea helper
        from tests.e2e.gitea_cleanup import GiteaTestHelper
        gitea = GiteaTestHelper(
            api_url=settings.GITEA_API,
            api_user=settings.GITEA_API_USER,
            api_password=settings.GITEA_API_PASSWORD,
            owner=repo_owner,
            repo=test_repo,
        )

        # Reset state
        self.stdout.write('  Flushing database...')
        call_command('flush', '--no-input', verbosity=0)
        call_command('loaddata', 'status', verbosity=0)

        # Create dev user
        from django.contrib.auth.models import User
        from users.models import GiteaUser
        user, _ = User.objects.get_or_create(
            username='devuser', defaults={'email': 'devuser@localhost'},
        )
        gitea_user, _ = GiteaUser.objects.get_or_create(
            user=user,
            defaults={'gitea_id': 99999, 'username': 'devuser', 'email': 'devuser@localhost'},
        )

        # Create authenticated API client
        from knox.models import AuthToken
        _, token = AuthToken.objects.create(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        self.stdout.write('  Resetting Gitea repo...')
        try:
            gitea.full_reset()
            self.stdout.write(self.style.SUCCESS('  Setup complete.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Gitea reset failed: {e}'))
            self._restore_settings(original_repo, original_repo_owner, original_celery_eager)
            return

        # ── Phase 1: TestFunction Flow ──────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 1: TestFunction Flow ═══'))
        p1 = Phase('TestFunction', self.stdout, verbose)
        phases.append(p1)

        try:
            tf_dir = FIXTURES_DIR
            # Create a temp dir structure for testfunction upload
            import tempfile, shutil
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                shutil.copy(FIXTURES_DIR / 'sample_testfunction.py', tmpdir / 'standard.py')
                shutil.copy(FIXTURES_DIR / 'sample_requirements.txt', tmpdir / 'requirements.txt')

                pr = gitea.create_pr_testfunction('standard', str(tmpdir))
                p1.check(pr is not None, 'PR created for testfunction')

                # Fire webhook (opened)
                payload = gitea.build_webhook_payload(pr, action='opened')
                resp = client.post('/internal/gitea/webhook/', payload, format='json')
                p1.check(resp.status_code == 200, f'Webhook opened accepted (HTTP {resp.status_code})')

                # Check Request created
                from experiments.models import Request as RequestModel
                time.sleep(1)
                req_exists = RequestModel.objects.filter(
                    title__icontains='testfunction',
                ).exists()
                p1.check(req_exists, 'Request created in DB')

                # Merge PR (wait for Gitea to be ready)
                time.sleep(2)
                gitea.merge_pr(pr.number)
                time.sleep(2)

                # Re-fetch PR to get merged state
                merged_pr = gitea.repo_api.repo_get_pull_request(
                    owner=repo_owner, repo=test_repo, index=pr.number,
                )
                payload = gitea.build_webhook_payload(merged_pr, action='closed')
                payload['pull_request']['merged'] = True
                resp = client.post('/internal/gitea/webhook/', payload, format='json')
                p1.check(resp.status_code == 200, f'Webhook merged accepted (HTTP {resp.status_code})')

                # Verify published
                time.sleep(1)
                from experiments.models import TestfunctionSet
                tf_set = TestfunctionSet.objects.filter(name='standard').first()
                p1.check(tf_set is not None, 'TestfunctionSet created')
                if tf_set:
                    p1.check(tf_set.published, 'TestfunctionSet published')
                    p1.check(tf_set.testfunctions.exists(), 'Has TestFunctions')
        except Exception as e:
            p1.check(False, f'Phase 1 error: {e}')

        if interactive:
            action = self._pause('Phase 1: TestFunction')
            if action == 'revert':
                self._cleanup_and_exit(gitea, skip_cleanup, original_repo, original_repo_owner, original_celery_eager, phases, start_time)
                return
            elif action == 'stop':
                self._restore_settings(original_repo, original_repo_owner, original_celery_eager)
                return

        # ── Phase 2: Environment Flow ───────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 2: Environment Flow ═══'))
        p2 = Phase('Environment', self.stdout, verbose)
        phases.append(p2)

        try:
            pr = gitea.create_pr_environment('testenv', str(FIXTURES_DIR / 'sample_environment.yml'))
            p2.check(pr is not None, 'PR created for environment')

            payload = gitea.build_webhook_payload(pr, action='opened')
            resp = client.post('/internal/gitea/webhook/', payload, format='json')
            p2.check(resp.status_code == 200, f'Webhook opened accepted (HTTP {resp.status_code})')

            time.sleep(1)
            req_exists = RequestModel.objects.filter(title__icontains='environment').exists()
            p2.check(req_exists, 'Request created in DB')

            time.sleep(2)
            gitea.merge_pr(pr.number)
            time.sleep(2)

            merged_pr = gitea.repo_api.repo_get_pull_request(
                owner=repo_owner, repo=test_repo, index=pr.number,
            )
            payload = gitea.build_webhook_payload(merged_pr, action='closed')
            payload['pull_request']['merged'] = True
            resp = client.post('/internal/gitea/webhook/', payload, format='json')
            p2.check(resp.status_code == 200, f'Webhook merged accepted (HTTP {resp.status_code})')

            time.sleep(1)
            from experiments.models import Environment
            env = Environment.objects.filter(published=True).first()
            p2.check(env is not None, 'Environment created and published')
            if env:
                p2.check(env.os_info is not None, 'Has OsInfo')
        except Exception as e:
            p2.check(False, f'Phase 2 error: {e}')

        if interactive:
            action = self._pause('Phase 2: Environment')
            if action == 'revert':
                self._cleanup_and_exit(gitea, skip_cleanup, original_repo, original_repo_owner, original_celery_eager, phases, start_time)
                return
            elif action == 'stop':
                self._restore_settings(original_repo, original_repo_owner, original_celery_eager)
                return

        # ── Phase 3: Experiment Flow ────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 3: Experiment Flow ═══'))
        p3 = Phase('Experiment', self.stdout, verbose)
        phases.append(p3)

        try:
            import tempfile, shutil
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                shutil.copy(FIXTURES_DIR / 'sample_action.py', tmpdir / 'action.py')
                shutil.copy(FIXTURES_DIR / 'sample_testset.yml', tmpdir / 'testset.yml')
                shutil.copy(FIXTURES_DIR / 'sample_metadata.yml', tmpdir / 'metadata.yml')

                pr = gitea.create_pr_experiment('test-experiment', str(tmpdir))
                p3.check(pr is not None, 'PR created for experiment')

                payload = gitea.build_webhook_payload(pr, action='opened')
                resp = client.post('/internal/gitea/webhook/', payload, format='json')
                p3.check(resp.status_code == 200, f'Webhook opened accepted (HTTP {resp.status_code})')

                time.sleep(1)
                req_exists = RequestModel.objects.filter(title__icontains='experiment').exists()
                p3.check(req_exists, 'Request created in DB')

                gitea.merge_pr(pr.number)
                time.sleep(1)

                merged_pr = gitea.repo_api.repo_get_pull_request(
                    owner=repo_owner, repo=test_repo, index=pr.number,
                )
                payload = gitea.build_webhook_payload(merged_pr, action='closed')
                payload['pull_request']['merged'] = True
                resp = client.post('/internal/gitea/webhook/', payload, format='json')
                p3.check(resp.status_code == 200, f'Webhook merged accepted (HTTP {resp.status_code})')

                time.sleep(1)
                from experiments.models import Experiment
                exp = Experiment.objects.filter(published=True).first()
                p3.check(exp is not None, 'Experiment created and published')
                if exp:
                    p3.check(exp.environments.exists(), 'Linked to environments')
                    p3.check(exp.abstract_tests.exists(), 'Linked to abstract tests')
        except Exception as e:
            p3.check(False, f'Phase 3 error: {e}')

        if interactive:
            action = self._pause('Phase 3: Experiment (all entities published)')
            if action == 'revert':
                self._cleanup_and_exit(gitea, skip_cleanup, original_repo, original_repo_owner, original_celery_eager, phases, start_time)
                return
            elif action == 'stop':
                self._restore_settings(original_repo, original_repo_owner, original_celery_eager)
                return

        # ── Phase 4: Run Publish Flow ───────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 4: Run Publish Flow ═══'))
        p4 = Phase('Run Publish', self.stdout, verbose)
        phases.append(p4)

        try:
            from experiments.models import Experiment, Environment, Status, ExperimentRun, generate_ulid

            exp = Experiment.objects.filter(published=True).first()
            env = Environment.objects.filter(published=True).first()

            if exp and env:
                finished_status = Status.objects.get(name='finished')
                success_status = Status.objects.get(name='success')
                run_ulid = generate_ulid()

                abstract_test = exp.abstract_tests.first()
                events = [
                    {
                        'ulid': generate_ulid(),
                        'category': 'command',
                        'status': 'finished',
                        'error': '',
                        'event_group_id': '1',
                        'timestamp': timezone.now().isoformat(),
                        'action_type': 'command',
                        'action_id': 'setup',
                        'action_data': '{"command": "echo setup", "returncode": 0, "stdout": "setup"}',
                    },
                    {
                        'ulid': generate_ulid(),
                        'category': 'command',
                        'status': 'finished',
                        'error': '',
                        'event_group_id': '2',
                        'timestamp': timezone.now().isoformat(),
                        'action_type': 'command',
                        'action_id': 'run-test',
                        'action_data': '{"command": "echo test", "returncode": 0, "stdout": "test"}',
                    },
                ]
                if abstract_test:
                    events.append({
                        'ulid': generate_ulid(),
                        'category': 'test',
                        'status': 'finished',
                        'error': '',
                        'event_group_id': '3',
                        'timestamp': timezone.now().isoformat(),
                        'result': {
                            'status': 'success',
                            'details': 'Test passed',
                        },
                        'abstract_test_ulid': abstract_test.ulid,
                    })
                    events.append({
                        'ulid': generate_ulid(),
                        'category': 'error',
                        'status': 'finished',
                        'error': '',
                        'event_group_id': '4',
                        'timestamp': timezone.now().isoformat(),
                        'error_name': 'NonCriticalWarning',
                        'error_msg': 'Minor issue detected',
                    })

                metadata = json.dumps({
                    'ulid': run_ulid,
                    'experiment_ulid': exp.ulid,
                    'environment_ulid': env.ulid,
                    'status': 'finished',
                    'result_status': 'success',
                    'timestamp_start': timezone.now().isoformat(),
                    'timestamp_end': timezone.now().isoformat(),
                    'events': events,
                })

                resp = client.post('/api/run/publish/', {
                    'metadata': metadata,
                    'adarevm_log': SimpleUploadedFile('adarevm.log', b'E2E test log'),
                    'installations_log': SimpleUploadedFile('installations.log', b'E2E test log'),
                    'packagedump_log': SimpleUploadedFile('packagedump.log', b'E2E test log'),
                }, format='multipart')
                p4.check(resp.status_code == 201, f'Run published (HTTP {resp.status_code})')

                run = ExperimentRun.objects.filter(ulid=run_ulid).first()
                p4.check(run is not None, 'ExperimentRun exists in DB')
                if run:
                    p4.check(run.status == finished_status, 'Run status is finished')
                    event_count = len(run.events)
                    p4.check(event_count == len(events), f'Events created ({event_count})')

                # Verify via API (mock MinIO since it may not be configured)
                from unittest.mock import patch
                with patch('helperfunctions.minio.get_presigned_url', return_value='http://mock/file'), \
                     patch('experiments.serializers.get_presigned_url', return_value='http://mock/file'):
                    resp = client.get('/api/run/', {'limit': 100})
                    p4.check(resp.status_code == 200, 'Run list accessible')
                    p4.check(resp.data['count'] >= 1, 'Run appears in list')

                resp = client.get('/api/experiment/', {'limit': 100})
                p4.check(resp.status_code == 200, 'Experiment list accessible')

                if interactive:
                    action = self._pause('Phase 4: Run published (check run in GUI before deletion)')
                    if action == 'revert':
                        self._cleanup_and_exit(gitea, skip_cleanup, original_repo, original_repo_owner, original_celery_eager, phases, start_time)
                        return
                    elif action == 'stop':
                        self._restore_settings(original_repo, original_repo_owner, original_celery_eager)
                        return

                # Delete run
                resp = client.delete(f'/api/run/delete/run_{run_ulid}/')
                p4.check(resp.status_code == 204, f'Run deleted (HTTP {resp.status_code})')
                p4.check(
                    not ExperimentRun.objects.filter(ulid=run_ulid).exists(),
                    'Run removed from DB',
                )
            else:
                p4.check(False, 'No published experiment or environment to test with')
        except Exception as e:
            p4.check(False, f'Phase 4 error: {e}')

        # ── Phase 5: Stats Verification ─────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 5: Stats Verification ═══'))
        p5 = Phase('Stats', self.stdout, verbose)
        phases.append(p5)

        try:
            resp = client.get('/api/stats/')
            p5.check(resp.status_code == 200, 'Stats endpoint accessible')
            data = resp.data
            p5.check('experiment_count' in data, 'Has experiment_count')
            p5.check('environment_count' in data, 'Has environment_count')
            p5.check('testfunctionset_count' in data, 'Has testfunctionset_count')
            p5.check('run_count' in data, 'Has run_count')

            from experiments.models import Experiment, Environment, TestfunctionSet
            p5.check(
                data['experiment_count'] == Experiment.objects.count(),
                f'Experiment count matches ({data["experiment_count"]})',
            )
            p5.check(
                data['environment_count'] == Environment.objects.count(),
                f'Environment count matches ({data["environment_count"]})',
            )
        except Exception as e:
            p5.check(False, f'Phase 5 error: {e}')

        # ── Phase 6: Cleanup ────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Phase 6: Cleanup ═══'))
        if skip_cleanup:
            self.stdout.write('  Skipping cleanup (--skip-cleanup)')
        else:
            try:
                gitea.full_reset()
                self.stdout.write(self.style.SUCCESS('  Gitea repo cleaned up.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Cleanup failed: {e}'))

        # Restore settings
        self._restore_settings(original_repo, original_repo_owner, original_celery_eager)

        # ── Summary ─────────────────────────────────────────────────────
        self._print_summary(phases, start_time)
        all_passed = all(p.passed for p in phases)
        if not all_passed:
            self.stderr.write(self.style.ERROR('\nE2E TESTS FAILED'))
            raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS('\nAll E2E tests passed!'))

    def _cleanup_and_exit(self, gitea, skip_cleanup, repo, owner, celery_eager, phases, start_time):
        """Revert: clean up Gitea + DB, restore settings, print summary."""
        if not skip_cleanup:
            self.stdout.write(self.style.WARNING('  Reverting: cleaning up Gitea repo and flushing DB...'))
            try:
                gitea.full_reset()
                from django.core.management import call_command
                call_command('flush', '--no-input', verbosity=0)
                call_command('loaddata', 'status', verbosity=0)
                self.stdout.write(self.style.SUCCESS('  Reverted.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Revert failed: {e}'))
        self._restore_settings(repo, owner, celery_eager)
        self._print_summary(phases, start_time)
        raise SystemExit(2)

    def _print_summary(self, phases, start_time):
        elapsed = time.time() - start_time
        self.stdout.write(self.style.MIGRATE_HEADING(f'\n═══ Summary ({elapsed:.1f}s) ═══'))
        for phase in phases:
            style = self.style.SUCCESS if phase.passed else self.style.ERROR
            self.stdout.write(style(f'  {phase.summary}'))
        total_checks = sum(len(p.assertions) for p in phases)
        total_passed = sum(sum(1 for _, ok in p.assertions if ok) for p in phases)
        self.stdout.write(f'\n  Total: {total_passed}/{total_checks} checks passed')

    def _restore_settings(self, repo, owner, celery_eager):
        settings.GITEA_EXPERIMENTS_REPO = repo
        settings.GITEA_EXPERIMENTS_REPO_OWNER = owner
        settings.CELERY_TASK_ALWAYS_EAGER = celery_eager

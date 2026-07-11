import hashlib
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from experiments.models import (
    AbstractTest,
    ActionEvent,
    Environment,
    ErrorEvent,
    Experiment,
    ExperimentRun,
    Label,
    OsInfo,
    PostSetupInstallation,
    Request,
    Result,
    Status,
    Tag,
    TagScope,
    TestEvent,
    TestFunction,
    TestParameter,
    TestParameterEntry,
    TestfunctionSet,
    Tool,
)
from users.models import GiteaUser


def _hash(model, name):
    return hashlib.sha256(f'seed-{model}-{name}'.encode()).hexdigest()


class Command(BaseCommand):
    help = 'Seed rich sample data for local development'

    def handle(self, *args, **options):
        call_command('loaddata', 'status', verbosity=0)
        self.now = timezone.now()

        self._create_users()
        self._create_tags()
        self._create_os_infos()
        self._create_installations()
        self._create_environments()
        self._create_testfunction_sets()
        self._create_tools_and_params()
        self._create_abstract_tests()
        self._create_experiments()
        self._create_runs_and_events()
        self._create_requests()
        self._print_summary()

    # ── Users ───────────────────────────────────────────────────────────
    def _create_users(self):
        self.gitea_users = {}
        for i, (uname, email) in enumerate([
            ('devuser', 'devuser@localhost'),
            ('researcher1', 'researcher1@localhost'),
            ('researcher2', 'researcher2@localhost'),
        ], start=1):
            user, _ = User.objects.get_or_create(
                username=uname, defaults={'email': email},
            )
            gu, _ = GiteaUser.objects.get_or_create(
                user=user,
                defaults={'gitea_id': 99990 + i, 'username': uname, 'email': email},
            )
            self.gitea_users[uname] = gu
        self.stdout.write(f'  Users: {", ".join(self.gitea_users)}')

    # ── Tags ────────────────────────────────────────────────────────────
    def _create_tags(self):
        scope_defs = [
            ('tool', '#1e40af'),
            ('artifact', '#166534'),
            ('goal', '#6b21a8'),
            ('platform', '#9a3412'),
        ]
        self.scopes = {}
        for name, color in scope_defs:
            scope, _ = TagScope.objects.get_or_create(
                name=name, defaults={'color': color, 'is_predefined': True},
            )
            self.scopes[name] = scope

        tag_defs = [
            ('tool', ['Autopsy', 'FTK Imager', 'Volatility', 'Wireshark']),
            ('artifact', ['Registry', 'Filesystem', 'Memory', 'Network']),
            ('goal', ['tool-test', 'artifact-extraction', 'acquisition']),
            ('platform', ['Windows', 'Linux']),
        ]
        self.tags = {}
        for scope_name, values in tag_defs:
            for val in values:
                tag, _ = Tag.objects.get_or_create(
                    scope=self.scopes[scope_name], value=val,
                    defaults={'name': f'{scope_name}:{val}'},
                )
                self.tags[tag.name] = tag

        # unscoped tags
        for val in ('beta', 'deprecated'):
            tag, _ = Tag.objects.get_or_create(
                scope=None, value=val, defaults={'name': val},
            )
            self.tags[val] = tag

        self.stdout.write(f'  Tags: {len(self.tags)}')

    # ── OsInfo ──────────────────────────────────────────────────────────
    def _create_os_infos(self):
        os_defs = [
            ('Linux', 'Ubuntu', '22.04', 'en_US', 'x86_64'),
            ('Linux', 'Debian', '12', 'en_US', 'x86_64'),
            ('Windows', 'Windows', '10 21H2', 'en_US', 'x86_64'),
            ('Windows', 'Windows', '11 23H2', 'en_US', 'x86_64'),
        ]
        self.os_infos = {}
        for os_name, dist, ver, lang, arch in os_defs:
            oi, _ = OsInfo.objects.get_or_create(
                os=os_name, distribution=dist, version=ver,
                defaults={'language': lang, 'architecture': arch},
            )
            self.os_infos[f'{dist}-{ver}'] = oi
        self.stdout.write(f'  OsInfos: {len(self.os_infos)}')

    # ── PostSetupInstallations ──────────────────────────────────────────
    def _create_installations(self):
        inst_defs = [
            ('forensic-tools', 'Install forensic toolkit', 'apt install autopsy sleuthkit -y'),
            ('network-tools', 'Install network analysis tools', 'apt install wireshark tshark -y'),
            ('volatility', 'Install Volatility framework', 'pip install volatility3'),
        ]
        self.installations = {}
        for name, desc, cmd in inst_defs:
            inst, _ = PostSetupInstallation.objects.get_or_create(
                name=name, defaults={'description': desc, 'command': cmd},
            )
            self.installations[name] = inst
        self.stdout.write(f'  Installations: {len(self.installations)}')

    # ── Environments ────────────────────────────────────────────────────
    def _create_environments(self):
        gu = self.gitea_users['devuser']
        env_defs = [
            ('ubuntu-desktop', 'ubuntu/jammy64', 'Ubuntu 22.04 desktop',
             'Ubuntu-22.04', ['platform:Linux'], ['forensic-tools']),
            ('ubuntu-server', 'ubuntu/jammy64', 'Ubuntu 22.04 server',
             'Ubuntu-22.04', ['platform:Linux'], ['network-tools']),
            ('debian-forensics', 'debian/bookworm64', 'Debian 12 forensics workstation',
             'Debian-12', ['platform:Linux', 'beta'], ['forensic-tools', 'volatility']),
            ('win10-workstation', 'gusztavvargadr/windows-10', 'Windows 10 workstation',
             'Windows-10 21H2', ['platform:Windows'], []),
            ('win11-workstation', 'gusztavvargadr/windows-11', 'Windows 11 workstation',
             'Windows-11 23H2', ['platform:Windows'], []),
            ('debian-minimal', 'debian/bookworm64', 'Debian 12 minimal',
             'Debian-12', ['platform:Linux'], []),
        ]
        self.environments = {}
        for name, box, desc, os_key, tag_names, inst_names in env_defs:
            env, created = Environment.objects.get_or_create(
                name=name,
                defaults={
                    'vagrantbox': box,
                    'description': desc,
                    'os_info': self.os_infos[os_key],
                    'file': f'https://example.com/environments/{name}.yml',
                    'sha256hash': _hash('env', name),
                    'published_by': gu,
                    'created_by': gu,
                    'published_at': self.now,
                    'created_at': self.now,
                    'published': True,
                },
            )
            if created:
                env.tags.set([self.tags[t] for t in tag_names])
                env.post_setup_installations.set(
                    [self.installations[n] for n in inst_names]
                )
            self.environments[name] = env
        self.stdout.write(f'  Environments: {len(self.environments)}')

    # ── TestfunctionSets + TestFunctions ────────────────────────────────
    def _create_testfunction_sets(self):
        gu = self.gitea_users['devuser']
        tfs_defs = [
            ('file-system-checks', 'File and directory existence checks',
             [('is_file', 'IsFile', 'Check if a file exists'),
              ('is_directory', 'IsDirectory', 'Check if a directory exists'),
              ('file_contains', 'FileContains', 'Check if file contains text')],
             ['goal:tool-test']),
            ('gui-interaction-tests', 'GUI automation tests',
             [('gui_find_element', 'GuiFindElement', 'Find a GUI element'),
              ('gui_click_target', 'GuiClickTarget', 'Click a GUI target')],
             ['goal:tool-test', 'beta']),
            ('network-analysis-checks', 'Network connectivity and capture checks',
             [('is_listening', 'IsListening', 'Check if port is listening'),
              ('has_connection', 'HasConnection', 'Check active connection'),
              ('packet_capture', 'PacketCapture', 'Verify packet capture')],
             ['goal:artifact-extraction']),
        ]
        self.tfs = {}
        self.testfunctions = {}
        for tfs_name, desc, funcs, tag_names in tfs_defs:
            tfs, created = TestfunctionSet.objects.get_or_create(
                name=tfs_name,
                defaults={
                    'description': desc,
                    'file': f'https://example.com/testfunctions/{tfs_name}.py',
                    'requirements_file': f'https://example.com/testfunctions/{tfs_name}-req.txt',
                    'sha256hash': _hash('tfs', tfs_name),
                    'sha256testfunctionset': _hash('tfs-code', tfs_name),
                    'sha256requirements': _hash('tfs-req', tfs_name),
                    'published_by': gu,
                    'created_by': gu,
                    'published_at': self.now,
                    'created_at': self.now,
                    'published': True,
                },
            )
            if created:
                tfs.tags.set([self.tags[t] for t in tag_names])
            self.tfs[tfs_name] = tfs
            for fn_name, fn_type, fn_desc in funcs:
                tf, _ = TestFunction.objects.get_or_create(
                    name=fn_name, testfunction_set=tfs,
                    defaults={'type': fn_type, 'description': fn_desc},
                )
                self.testfunctions[fn_name] = tf
        self.stdout.write(f'  TestfunctionSets: {len(self.tfs)}, TestFunctions: {len(self.testfunctions)}')

    # ── Tools + TestParameters ──────────────────────────────────────────
    def _create_tools_and_params(self):
        tool_defs = [
            ('Autopsy', 'autopsy'),
            ('Volatility', 'vol3'),
            ('Wireshark', 'wireshark'),
        ]
        self.tools = {}
        for name, cmd in tool_defs:
            tool, _ = Tool.objects.get_or_create(name=name, defaults={'command': cmd})
            self.tools[name] = tool

        param_defs = [
            ('path', 'string', 'File or directory path'),
            ('content', 'string', 'Expected content'),
            ('timeout', 'integer', 'Timeout in seconds'),
            ('target', 'string', 'GUI target identifier'),
        ]
        self.params = {}
        for name, dtype, desc in param_defs:
            p, _ = TestParameter.objects.get_or_create(
                name=name, defaults={'dtype': dtype, 'description': desc},
            )
            self.params[name] = p
        self.stdout.write(f'  Tools: {len(self.tools)}, Params: {len(self.params)}')

    # ── AbstractTests ───────────────────────────────────────────────────
    def _create_abstract_tests(self):
        at_defs = [
            ('check-autopsy-output', 'Verify Autopsy output file',
             'is_file', 'Autopsy', [('path', '/tmp/autopsy/output.html')]),
            ('check-volatility-dump', 'Verify Volatility memory dump',
             'is_file', 'Volatility', [('path', '/tmp/vol/memdump.raw')]),
            ('check-capture-file', 'Verify pcap capture exists',
             'is_file', 'Wireshark', [('path', '/tmp/capture.pcap')]),
            ('check-forensic-dir', 'Verify forensic output directory',
             'is_directory', None, [('path', '/tmp/forensics/')]),
            ('gui-find-autopsy', 'Find Autopsy window',
             'gui_find_element', 'Autopsy', [('target', 'Autopsy Browser')]),
            ('gui-click-analyze', 'Click analyze button',
             'gui_click_target', 'Autopsy', [('target', 'Analyze')]),
        ]
        self.abstract_tests = {}
        for at_name, desc, tf_name, tool_name, params in at_defs:
            # Create parameter entries
            entries = []
            for pname, pval in params:
                entry, _ = TestParameterEntry.objects.get_or_create(
                    parameter=self.params[pname], value=pval,
                )
                entries.append(entry)

            at, created = AbstractTest.objects.get_or_create(
                name=at_name,
                testfunction=self.testfunctions[tf_name],
                defaults={
                    'description': desc,
                },
            )
            if created:
                at.parameters.set(entries)
                if tool_name:
                    at.tools.add(self.tools[tool_name])
            self.abstract_tests[at_name] = at
        self.stdout.write(f'  AbstractTests: {len(self.abstract_tests)}')

    # ── Experiments ─────────────────────────────────────────────────────
    def _create_experiments(self):
        gu = self.gitea_users
        exp_defs = [
            ('autopsy-file-analysis',
             'Verify Autopsy file analysis output',
             ['tool:Autopsy', 'artifact:Filesystem', 'goal:tool-test'],
             ['ubuntu-desktop'], ['check-autopsy-output', 'check-forensic-dir'], 'devuser'),
            ('volatility-memory-dump',
             'Test Volatility memory dump extraction',
             ['tool:Volatility', 'artifact:Memory', 'goal:tool-test'],
             ['ubuntu-desktop', 'debian-forensics'], ['check-volatility-dump'], 'researcher1'),
            ('wireshark-capture',
             'Capture and verify network traffic',
             ['tool:Wireshark', 'artifact:Network', 'goal:artifact-extraction'],
             ['ubuntu-server'], ['check-capture-file'], 'devuser'),
            ('registry-forensics',
             'Extract and analyze Windows registry hives',
             ['artifact:Registry', 'platform:Windows'],
             ['win10-workstation'], ['check-forensic-dir'], 'researcher2'),
            ('full-forensic-workflow',
             'End-to-end forensic acquisition and analysis',
             ['tool:Autopsy', 'tool:Volatility', 'artifact:Filesystem', 'artifact:Memory', 'goal:acquisition'],
             ['ubuntu-desktop', 'debian-forensics', 'win10-workstation'],
             ['check-autopsy-output', 'check-volatility-dump', 'check-forensic-dir'], 'devuser'),
            ('autopsy-gui-test',
             'Test Autopsy GUI interaction',
             ['tool:Autopsy', 'goal:tool-test'],
             ['win11-workstation'], ['gui-find-autopsy', 'gui-click-analyze'], 'researcher1'),
            ('network-baseline',
             'Establish network baseline captures',
             ['artifact:Network', 'goal:artifact-extraction'],
             ['ubuntu-server', 'debian-minimal'], ['check-capture-file'], 'devuser'),
            ('memory-acquisition-linux',
             'Linux memory acquisition workflow',
             ['tool:Volatility', 'artifact:Memory', 'platform:Linux', 'goal:acquisition'],
             ['ubuntu-desktop', 'debian-forensics'], ['check-volatility-dump'], 'researcher2'),
            ('filesystem-integrity',
             'Verify filesystem integrity after acquisition',
             ['artifact:Filesystem', 'goal:artifact-extraction'],
             ['ubuntu-desktop', 'debian-minimal'], ['check-forensic-dir'], 'devuser'),
            ('windows-registry-deep',
             'Deep Windows registry analysis',
             ['artifact:Registry', 'platform:Windows', 'goal:tool-test'],
             ['win10-workstation', 'win11-workstation'], ['check-forensic-dir'], 'researcher1'),
            ('wireshark-filters-test',
             'Test Wireshark display filter configurations',
             ['tool:Wireshark', 'goal:tool-test'],
             ['ubuntu-server'], ['check-capture-file'], 'devuser'),
            ('cross-platform-forensics',
             'Cross-platform forensic toolchain test',
             ['tool:Autopsy', 'artifact:Filesystem', 'platform:Windows', 'platform:Linux'],
             ['ubuntu-desktop', 'win10-workstation'],
             ['check-autopsy-output', 'check-forensic-dir'], 'researcher2'),
            ('deprecated-volatility-test',
             'Legacy Volatility 2 compatibility test',
             ['tool:Volatility', 'deprecated'],
             ['debian-forensics'], ['check-volatility-dump'], 'devuser'),
            ('beta-gui-automation',
             'Beta GUI automation suite',
             ['tool:Autopsy', 'beta'],
             ['win11-workstation'], ['gui-find-autopsy', 'gui-click-analyze'], 'researcher1'),
            ('ftk-imager-acquisition',
             'FTK Imager disk acquisition test',
             ['tool:FTK Imager', 'artifact:Filesystem', 'goal:acquisition'],
             ['win10-workstation'], ['check-forensic-dir'], 'researcher2'),
        ]
        self.experiments = {}
        for name, desc, tag_names, env_names, test_names, user_key in exp_defs:
            exp, created = Experiment.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'playbook_file': f'https://example.com/experiments/{name}/playbook.yml',
                    'metadata_file': f'https://example.com/experiments/{name}/metadata.yml',
                    'sha256hash': _hash('exp', name),
                    'sha256playbook': _hash('exp-playbook', name),
                    'published_by': gu[user_key],
                    'created_by': gu[user_key],
                    'published_at': self.now,
                    'created_at': self.now,
                    'published': True,
                },
            )
            if created:
                exp.tags.set([self.tags[t] for t in tag_names])
                exp.environments.set([self.environments[e] for e in env_names])
                exp.abstract_tests.set([self.abstract_tests[t] for t in test_names])
            self.experiments[name] = exp
        self.stdout.write(f'  Experiments: {len(self.experiments)}')

    # ── Runs + Events ───────────────────────────────────────────────────
    def _create_runs_and_events(self):
        status_map = {s.name: s for s in Status.objects.all()}
        gu = self.gitea_users['devuser']

        # Count expected runs per (experiment, environment) for idempotency
        from collections import Counter

        # (experiment, environment, days_ago, run_status, result_status)
        run_defs = [
            ('autopsy-file-analysis', 'ubuntu-desktop', 28, 'finished', 'success'),
            ('autopsy-file-analysis', 'ubuntu-desktop', 14, 'finished', 'success'),
            ('autopsy-file-analysis', 'ubuntu-desktop', 2, 'finished', 'success'),
            ('volatility-memory-dump', 'ubuntu-desktop', 25, 'finished', 'success'),
            ('volatility-memory-dump', 'debian-forensics', 20, 'finished', 'failed'),
            ('volatility-memory-dump', 'debian-forensics', 10, 'finished', 'success'),
            ('wireshark-capture', 'ubuntu-server', 22, 'finished', 'success'),
            ('wireshark-capture', 'ubuntu-server', 5, 'finished', 'failed'),
            ('registry-forensics', 'win10-workstation', 18, 'finished', 'success'),
            ('full-forensic-workflow', 'ubuntu-desktop', 15, 'finished', 'success'),
            ('full-forensic-workflow', 'debian-forensics', 12, 'finished', 'failed'),
            ('full-forensic-workflow', 'win10-workstation', 8, 'finished', 'success'),
            ('autopsy-gui-test', 'win11-workstation', 16, 'finished', 'success'),
            ('network-baseline', 'ubuntu-server', 21, 'finished', 'success'),
            ('network-baseline', 'debian-minimal', 11, 'finished', 'failed'),
            ('memory-acquisition-linux', 'ubuntu-desktop', 19, 'finished', 'success'),
            ('memory-acquisition-linux', 'debian-forensics', 7, 'finished', 'success'),
            ('filesystem-integrity', 'ubuntu-desktop', 13, 'finished', 'success'),
            ('windows-registry-deep', 'win10-workstation', 9, 'finished', 'failed'),
            ('windows-registry-deep', 'win11-workstation', 4, 'finished', 'success'),
            ('wireshark-filters-test', 'ubuntu-server', 6, 'finished', 'success'),
            ('cross-platform-forensics', 'ubuntu-desktop', 17, 'finished', 'failed'),
            ('cross-platform-forensics', 'win10-workstation', 3, 'finished', 'success'),
            ('deprecated-volatility-test', 'debian-forensics', 1, 'running', 'none'),
            ('beta-gui-automation', 'win11-workstation', 0, 'pending', 'none'),
        ]

        # Build expected counts per (exp, env) pair
        expected_counts = Counter((e, v) for e, v, *_ in run_defs)

        self.runs = []
        for exp_name, env_name, days_ago, run_status, result_status in run_defs:
            exp = self.experiments[exp_name]
            env = self.environments[env_name]

            # Skip if this (exp, env) pair already has enough runs
            existing = ExperimentRun.objects.filter(experiment=exp, environment=env).count()
            target = expected_counts[(exp_name, env_name)]
            if existing >= target:
                # Grab the latest existing run for reference
                run = ExperimentRun.objects.filter(
                    experiment=exp, environment=env,
                ).order_by('-timestamp_start').first()
                self.runs.append(run)
                continue

            ts_start = self.now - timedelta(days=days_ago, hours=1)
            ts_end = ts_start + timedelta(minutes=15)

            run = ExperimentRun(
                experiment=exp,
                environment=env,
                published_by=gu,
                published_at=ts_start,
                timestamp_start=ts_start,
                timestamp_end=ts_end,
                status=status_map[run_status],
                result_status=status_map[result_status],
            )
            run.adarevm_logfile.save(
                f'{exp_name}-adarevm.log', ContentFile(b'placeholder'), save=False,
            )
            run.installations_logfile.save(
                f'{exp_name}-installations.log', ContentFile(b'placeholder'), save=False,
            )
            run.packagedump_logfile.save(
                f'{exp_name}-packagedump.log', ContentFile(b'placeholder'), save=False,
            )
            run.save()
            self.runs.append(run)

            # Create events for finished runs
            if run_status == 'finished':
                self._create_events_for_run(run, result_status, exp_name, status_map)

        self.stdout.write(f'  ExperimentRuns: {len(self.runs)}')

    def _create_events_for_run(self, run, result_status, exp_name, status_map):
        import json
        ts = run.timestamp_start + timedelta(minutes=1)
        group = 0

        # ActionEvent: setup command
        if not ActionEvent.objects.filter(run=run, event_group_id='0').exists():
            ActionEvent.objects.create(
                run=run, event_group_id='0', timestamp=ts,
                category='command', status=status_map['finished'],
                action_type='command', action_id='setup-environment',
                action_data=json.dumps({'command': f'vagrant up {exp_name}', 'returncode': 0, 'stdout': 'Environment ready.'}),
                success=True,
            )

        # ActionEvent: execute command
        group = 1
        ts = ts + timedelta(minutes=3)
        if not ActionEvent.objects.filter(run=run, event_group_id='1').exists():
            rc = 0 if result_status == 'success' else 1
            ActionEvent.objects.create(
                run=run, event_group_id='1', timestamp=ts,
                category='command', status=status_map['finished'],
                action_type='command', action_id='run-tests',
                action_data=json.dumps({'command': f'pytest /tests/{exp_name}/', 'returncode': rc, 'stdout': 'Tests completed.' if result_status == 'success' else 'FAILED'}),
                success=(result_status == 'success'),
            )

        # TestEvent for each abstract test
        group = 2
        ts = ts + timedelta(minutes=2)
        for at in run.experiment.abstract_tests.all():
            if not TestEvent.objects.filter(run=run, abstracttest=at).exists():
                test_status = status_map[result_status]
                result, _ = Result.objects.get_or_create(
                    status=test_status,
                    defaults={'details': f'Test {at.name}: {result_status}'},
                )
                TestEvent.objects.create(
                    run=run, event_group_id=str(group), timestamp=ts,
                    category='test', status=test_status,
                    abstracttest=at, result=result,
                    success=(result_status == 'success'),
                )
                group += 1
                ts = ts + timedelta(seconds=30)

        # ErrorEvent for failed runs
        if result_status == 'failed':
            if not ErrorEvent.objects.filter(run=run).exists():
                ErrorEvent.objects.create(
                    run=run, event_group_id=str(group), timestamp=ts,
                    category='error', status=status_map['error'],
                    error_name='AssertionError',
                    error_msg=f'Test assertion failed in {exp_name}',
                    success=False,
                )
                group += 1

        # Action events for gui experiments
        if 'gui' in exp_name:
            ts = ts + timedelta(seconds=10)
            if not ActionEvent.objects.filter(run=run, action_type='find').exists():
                ActionEvent.objects.create(
                    run=run, event_group_id=str(group), timestamp=ts,
                    category='action', status=status_map['finished'],
                    action_type='find', action_id='find-window',
                    action_data=json.dumps({'objective': 'Find application window', 'positions': '100,200'}),
                    success=True,
                )
                group += 1
            ts = ts + timedelta(seconds=5)
            if not ActionEvent.objects.filter(run=run, action_type='click').exists():
                ActionEvent.objects.create(
                    run=run, event_group_id=str(group), timestamp=ts,
                    category='action', status=status_map['finished'],
                    action_type='click', action_id='click-analyze',
                    action_data=json.dumps({'target': 'Analyze Button', 'clicktype': 'single'}),
                    success=True,
                )

    # ── Requests ────────────────────────────────────────────────────────
    def _create_requests(self):
        label_defs = [
            (1001, 'enhancement', '0075ca', 'New feature or improvement'),
            (1002, 'bug', 'd73a4a', 'Something is broken'),
            (1003, 'review-needed', 'fbca04', 'Needs reviewer attention'),
            (1004, 'urgent', 'b60205', 'High priority'),
        ]
        labels = {}
        for gid, name, color, desc in label_defs:
            lbl, _ = Label.objects.get_or_create(
                gitea_label_id=gid,
                defaults={'name': name, 'color': color, 'description': desc},
            )
            labels[name] = lbl

        exp_ct = ContentType.objects.get_for_model(Experiment)
        env_ct = ContentType.objects.get_for_model(Environment)

        gu = self.gitea_users
        exp_list = list(self.experiments.values())
        env_list = list(self.environments.values())

        req_defs = [
            ('Add autopsy-file-analysis experiment', 'create', exp_ct, exp_list[0],
             None, None, 'open', 101, ['enhancement'], 'researcher1', 5),
            ('Update volatility-memory-dump', 'modify', exp_ct, exp_list[1],
             exp_ct, exp_list[1], 'open', 102, ['enhancement', 'review-needed'], 'devuser', 4),
            ('Fix wireshark-capture config', 'modify', exp_ct, exp_list[2],
             exp_ct, exp_list[2], 'closed', 103, ['bug'], 'researcher2', 10),
            ('Add win10-workstation environment', 'create', env_ct, env_list[3],
             None, None, 'closed', 104, ['enhancement'], 'devuser', 8),
            ('Update ubuntu-desktop packages', 'modify', env_ct, env_list[0],
             env_ct, env_list[0], 'open', 105, ['review-needed'], 'researcher1', 3),
            ('Fix registry-forensics errors', 'modify', exp_ct, exp_list[3],
             exp_ct, exp_list[3], 'open', 106, ['bug', 'urgent'], 'researcher2', 1),
            ('Add full-forensic-workflow', 'create', exp_ct, exp_list[4],
             None, None, 'closed', 107, ['enhancement'], 'devuser', 15),
            ('Add debian-forensics environment', 'create', env_ct, env_list[2],
             None, None, 'closed', 108, ['enhancement'], 'researcher1', 12),
        ]

        count = 0
        for (title, action, obj_ct, obj, old_ct, old_obj,
             pr_status, pr_num, label_names, requester, days_ago) in req_defs:
            if Request.objects.filter(gitea_pr_number=pr_num).exists():
                count += 1
                continue
            creation = self.now - timedelta(days=days_ago)
            req = Request.objects.create(
                title=title,
                description=f'Seed request: {title}',
                creation_date=creation,
                last_change_date=creation + timedelta(hours=2),
                gitea_pr_url=f'https://gitea.example.com/adare/experiments/pulls/{pr_num}',
                gitea_pr_number=pr_num,
                gitea_pr_status=pr_status,
                action=action,
                objective_name=obj._meta.model_name,
                objective=obj_ct,
                object_id=obj.pk,
                old_objective_name=old_obj._meta.model_name if old_obj else None,
                old_objective=old_ct,
                old_object_id=old_obj.pk if old_obj else None,
                requester=gu[requester],
            )
            req.labels.set([labels[n] for n in label_names])
            count += 1
        self.stdout.write(f'  Requests: {count}')

    # ── Summary ─────────────────────────────────────────────────────────
    def _print_summary(self):
        self.stdout.write(self.style.SUCCESS(
            f'\nDev data seeded successfully:\n'
            f'  {User.objects.count()} users, '
            f'{Tag.objects.count()} tags, '
            f'{Environment.objects.count()} environments,\n'
            f'  {TestfunctionSet.objects.count()} testfunction sets, '
            f'{Experiment.objects.count()} experiments,\n'
            f'  {ExperimentRun.objects.count()} runs, '
            f'{Request.objects.count()} requests'
        ))

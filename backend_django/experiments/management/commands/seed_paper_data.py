"""Seed the paper's evaluation vocabulary (sections 5.1-5.5) into the local dev database.

Companion to `seed_dev_data`, not a replacement: only names, OS versions and result
statuses a reader of the ADARE paper recognises. Every hash, URL, timestamp and
logfile is fake -- the vocabulary and the outcomes are the real part. Source of truth:
`adare/paper/README.md`, the per-case-study `experiments/{1..5}_*/README.md`, and their
`metadata.yml` files.

The two seeders stay independent because `sha256hash` is unique on both `Experiment`
and `Environment` and this command hashes into its own `paper-` namespace (`_hash`).
`--purge` removes exactly the rows carrying those hashes.
"""

import hashlib
import json
from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Q
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
    """Hash into the paper namespace so rows never collide with `seed_dev_data`."""
    return hashlib.sha256(f'paper-{model}-{name}'.encode()).hexdigest()


# Demo password -- only ever set when DEBUG / MODE == 'development' (see _create_users).
DEMO_PASSWORD = 'paperdemo'  # noqa: S105 - local dev demo credential, never used in production

GITEA_BASE = 'https://gitea.example.com/adare'

# §5.4 -- the authoritative version lists, mirrored from
# `paper/experiments/4_autopsy_tool_regression_testing/provisioning/versions_solr{4,8}.txt`.
# 4.22.0 is deliberately absent: it is Figure 2's "Missing Version (X)".
AUTOPSY_SOLR4 = [
    '4.4.0', '4.4.1', '4.5.0', '4.6.0', '4.7.0', '4.8.0', '4.9.0', '4.9.1',
    '4.10.0', '4.11.0', '4.12.0', '4.13.0', '4.14.0', '4.15.0', '4.16.0', '4.17.0',
]
AUTOPSY_SOLR8 = [
    '4.18.0', '4.19.0', '4.19.1', '4.19.2', '4.19.3', '4.20.0', '4.21.0', '4.22.1',
]

# (name, description, os_key, days_ago, tags, installations)
ENV_DEFS = [
    ('win11-autopsy-solr8',
     'Windows 11 ARM64 + Autopsy 4.18.0-4.22.1 (Solr 8.6.3+). Built on the win11arm64-fresh '
     'base; per-version C:\\Program Files\\Autopsy-<v>. Run one Autopsy at a time.',
     'Windows-11 23H2', 0, ['platform:Windows', 'solr8'], ['autopsy-4.x', 'solr8']),
    ('win11-autopsy-solr4',
     'Windows 11 ARM64 + Autopsy 4.4.0-4.17.0 (Solr 4.10.3). Built on the win11arm64-fresh '
     'base; per-version C:\\Program Files\\Autopsy-<v>. Run one Autopsy at a time.',
     'Windows-11 23H2', 1, ['platform:Windows', 'solr4'], ['autopsy-4.x', 'solr4']),
    ('ubuntu-2404',
     'Ubuntu 24.04 LTS (Noble Numbat) desktop, GNOME / Nautilus.',
     'Ubuntu-24.04', 2, ['platform:Linux'], []),
    ('kubuntu-2404',
     'Kubuntu 24.04 (KDE Plasma on an Ubuntu 24.04 base), Dolphin file manager.',
     'Kubuntu-24.04', 3, ['platform:Linux'], []),
    ('fedora-42',
     'Fedora 42 Workstation (GNOME) with the KDE file managers available for the Dolphin '
     'and kioclient5 deletion paths.', 'Fedora-42', 4, ['platform:Linux'], []),
    ('ubuntu24043',
     'Ubuntu 24.04.3 LTS with liblnk-utils 20181227 and ExifTool 12.76 for LNK parsing.',
     'Ubuntu-24.04', 6, ['platform:Linux'], ['liblnk-utils', 'libimage-exiftool-perl']),
    ('win11',
     'Windows 11 with the Eric Zimmerman tools (PECmd, LECmd) in the shared tools directory.',
     'Windows-11 23H2', 7, ['platform:Windows'], ['eztools']),
    ('fedora-41',
     'Fedora 41 Workstation (GNOME) with the KDE file managers available for the Dolphin '
     'and kioclient5 deletion paths.', 'Fedora-41', 8, ['platform:Linux'], []),
    ('kubuntu-2204', 'Kubuntu 22.04 LTS (KDE Plasma / Dolphin).',
     'Kubuntu-22.04', 9, ['platform:Linux'], []),
    ('kubuntu-2004', 'Kubuntu 20.04 LTS (KDE Plasma / Dolphin).',
     'Kubuntu-20.04', 10, ['platform:Linux'], []),
    ('ubuntu-2204', 'Ubuntu 22.04 LTS (Jammy Jellyfish) desktop, GNOME / Nautilus, GLib 2.72.',
     'Ubuntu-22.04', 11, ['platform:Linux'], []),
    ('ubuntu-2004', 'Ubuntu 20.04 LTS (Focal Fossa) desktop, GNOME / Nautilus, GLib 2.64.',
     'Ubuntu-20.04', 12, ['platform:Linux'], []),
    ('ubuntu-1804', 'Ubuntu 18.04 LTS (Bionic Beaver) desktop, GNOME / Nautilus.',
     'Ubuntu-18.04', 14, ['platform:Linux'], []),
]

# §5.1 -- the trash-can deletion paths and the environments each one actually names
# (`paper/experiments/1_artifact_research/playbooks/*/metadata.yml`).
UBUNTU_ALL = ['ubuntu-1804', 'ubuntu-2004', 'ubuntu-2204', 'ubuntu-2404']
FEDORA_ALL = ['fedora-41', 'fedora-42']

TRASH_TESTS = ['trash_info_exists', 'trash_files_entry_exists', 'trash_original_absent']

# (name, tool_tag, environments, days_ago, description)
DELETION_DEFS = [
    ('deletefile_nautilus_by_click', 'tool:Nautilus', UBUNTU_ALL, 12,
     "Delete a file from three home subdirectories via the Nautilus (GNOME) context menu "
     "entry 'Move to Trash' and verify the resulting XDG trash can artifacts."),
    ('deletefile_nautilus_by_keypress', 'tool:Nautilus', UBUNTU_ALL, 14,
     'Delete a file from three home subdirectories by selecting it in Nautilus (GNOME) and '
     'pressing the Delete key, then verify the resulting XDG trash can artifacts.'),
    ('deletefile_dolphin_by_click', 'tool:Dolphin', FEDORA_ALL, 16,
     "Delete a file from three home subdirectories via the Dolphin (KDE) context menu entry "
     "'Move to Trash' and verify the resulting XDG trash can artifacts."),
    ('deletefile_dolphin_by_keypress', 'tool:Dolphin', FEDORA_ALL, 18,
     'Delete a file from three home subdirectories by selecting it in Dolphin (KDE) and '
     'pressing the Delete key, then verify the resulting XDG trash can artifacts.'),
    ('deletefile_gio_trash', 'tool:gio', UBUNTU_ALL + FEDORA_ALL, 20,
     "Delete a file from three home subdirectories with the GLib command line tool "
     "'gio trash' and verify the resulting XDG trash can artifacts."),
    ('deletefile_trashput', 'tool:trash-put', UBUNTU_ALL + FEDORA_ALL, 22,
     "Delete a file from three home subdirectories with 'trash-put' from trash-cli and "
     'verify the resulting XDG trash can artifacts.'),
    ('deletefile_kioclient5', 'tool:kioclient5', FEDORA_ALL, 25,
     "Delete a file from three home subdirectories with the KDE command line tool "
     "'kioclient5 move <path> trash:/' and verify the resulting XDG trash can artifacts."),
]

# §5.2 -- one interaction held constant, only the distribution varies.
# (env, days_ago, file_manager_tag, extra_tags, abstract_tests, result_status, detail)
XBEL_PRESENT_TESTS = ['xbel_exists', 'xbel_bookmark_href', 'xbel_visited_subsecond_precision']
XBEL_DEFECT_TESTS = ['xbel_exists', 'xbel_bookmark_href', 'xbel_visited_is_epoch_minus_one']
XBEL_ABSENT_TESTS = ['xbel_absent_after_open']

XBEL_OK = 'recently-used.xbel present and correct; timestamps sub-second.'
XBEL_DEFECT = (
    "recently-used.xbel present, but 'visited' is 1969-12-31T23:59:59Z (the integer -1 "
    'sentinel) and all timestamps carry second-level precision only -- GLib 2.64.'
)
XBEL_ABSENT = (
    'recently-used.xbel absent after the same interaction (KDE Plasma / Dolphin).'
)

XBEL_DEFS = [
    ('kubuntu-2404', 2, 'tool:Dolphin', [], XBEL_PRESENT_TESTS, 'success', XBEL_OK,
     'Paper 5.2: open one document on Kubuntu 24.04 and validate the recently-used.xbel '
     'access metadata'),
    ('ubuntu-2404', 4, 'tool:Nautilus', [], XBEL_PRESENT_TESTS, 'success', XBEL_OK,
     'Paper 5.2: open one document on Ubuntu 24.04 and validate the recently-used.xbel '
     'access metadata'),
    ('ubuntu-2204', 5, 'tool:Nautilus', [], XBEL_PRESENT_TESTS, 'success', XBEL_OK,
     'Paper 5.2: open one document on Ubuntu 22.04 and validate the recently-used.xbel '
     'access metadata'),
    ('ubuntu-2004', 6, 'tool:Nautilus', ['defect-pin'], XBEL_DEFECT_TESTS, 'warning', XBEL_DEFECT,
     "Paper 5.2: open one document on Ubuntu 20.04 and pin the known 'visited' = integer -1 "
     'defect plus second-level timestamp precision'),
    ('kubuntu-2204', 7, 'tool:Dolphin', ['absent-artifact'], XBEL_ABSENT_TESTS, 'failed', XBEL_ABSENT,
     'Paper 5.2: open one document on Kubuntu 22.04 and assert recently-used.xbel is NOT '
     'created'),
    ('kubuntu-2004', 8, 'tool:Dolphin', ['absent-artifact'], XBEL_ABSENT_TESTS, 'failed', XBEL_ABSENT,
     'Paper 5.2: open one document on Kubuntu 20.04 and assert recently-used.xbel is NOT '
     'created'),
    ('fedora-42', 9, 'tool:Nautilus', [], XBEL_PRESENT_TESTS, 'success', XBEL_OK,
     'Open one document and validate that recently-used.xbel is created (belongs to paper '
     '5.1, see README)'),
]

# §5.5 -- (name, env, tool_tag, platform_tag, days_ago, result_status, detail, description)
LNK_DEFS = [
    ('lnk_lnkinfo_ubuntu2404', 'ubuntu24043', 'tool:lnkinfo', 'platform:Linux', 0, 'failed',
     'lnkinfo 20181227 rejected L2 and L3 on liblnk\'s strict ExtraData size constraint; '
     'no link fields recovered. L1 parsed.',
     'Cross-tool validation (paper section 5.5): parse three LNK samples with lnkinfo '
     '(liblnk-utils 20181227) on Ubuntu 24.04. L1 parses; L2/L3 are REJECTED on liblnk\'s '
     'strict ExtraData size constraint, and those two failures are asserted expectations.'),
    ('lnk_exiftool_ubuntu2404', 'ubuntu24043', 'tool:ExifTool', 'platform:Linux', 0, 'success',
     'ExifTool 12.76 parsed L1/L2/L3 and reported the appended data rather than failing '
     '(Verbosity Low).',
     'Cross-tool validation (paper section 5.5): parse three LNK samples with ExifTool 12.76 '
     'on Ubuntu 24.04. All three parse; the appended data on L2/L3 is reported rather than '
     'rejected.'),
    ('lnk_lecmd_windows11', 'win11', 'tool:LECmd', 'platform:Windows', 1, 'success',
     'LECmd 1.5.1 parsed L1/L2/L3 and recovered every link field (Verbosity High).',
     'Cross-tool validation (paper section 5.5): parse three LNK samples with LECmd 1.5.1 on '
     'Windows 11. All three parse, with the richest field coverage of the three parsers.'),
]

PECMD_NAME = 'pecmd'
PECMD_DESC = (
    'Tool validation of PECmd (paper section 5.3): launch regedit ten times and, after each '
    'execution, export the Prefetch directory with PECmd and assert both the run count and '
    'the last-run timestamp. State Transition Testing -- every step is checked.'
)

AUTOPSY_WARNING = (
    '352 action descriptions were silently discarded (playbook descriptions declared as '
    'siblings of the action key); the report sheets otherwise match the 4.4.0 baseline.'
)

# `--purge` matches these exactly; 201+ cannot clash with seed_dev_data's 101-108.
PAPER_PR_NUMBERS = list(range(201, 207))

# CLI case studies get no GUI find/click events.
CLI_EXPERIMENTS = {
    'deletefile_gio_trash', 'deletefile_trashput', 'deletefile_kioclient5', PECMD_NAME,
    'lnk_lnkinfo_ubuntu2404', 'lnk_exiftool_ubuntu2404', 'lnk_lecmd_windows11',
}


def autopsy_experiment_name(version):
    return f'autopsy_{version}_webhistory'


def paper_environment_names():
    return [d[0] for d in ENV_DEFS]


def paper_experiment_names():
    names = [d[0] for d in DELETION_DEFS]
    names += [f'open-single-text-file-{d[0]}' for d in XBEL_DEFS]
    names.append(PECMD_NAME)
    names += [autopsy_experiment_name(v) for v in AUTOPSY_SOLR4 + AUTOPSY_SOLR8]
    names += [d[0] for d in LNK_DEFS]
    return names


class Command(BaseCommand):
    help = "Seed the paper's evaluation case studies (§5.1-§5.5) for local demos"

    def add_arguments(self, parser):
        parser.add_argument(
            '--purge', action='store_true',
            help='Delete the paper demo rows instead of creating them.',
        )

    def handle(self, *args, **options):
        self.now = timezone.now()
        if options['purge']:
            self._purge()
            return

        call_command('loaddata', 'status', verbosity=0)

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
        # /home is behind requireAuth; the web app's dev route in is the passwordless
        # "Dev Login" button (POST /api/auth/dev/). The password below is for /admin/.
        allow_password = getattr(settings, 'MODE', '') == 'development' or settings.DEBUG
        self.gitea_users = {}
        for i, (uname, email) in enumerate([('paperauthor', 'paperauthor@localhost'),
                                            ('reviewer1', 'reviewer1@localhost')], start=1):
            user, _ = User.objects.get_or_create(
                username=uname, defaults={'email': email},
            )
            if allow_password:
                user.set_password(DEMO_PASSWORD)
                # /admin/ rejects non-staff accounts, so without this the password would
                # be a credential usable nowhere. reviewer1 stays an ordinary account.
                if uname == 'paperauthor':
                    user.is_staff = True
                    user.is_superuser = True
                user.save(update_fields=['password', 'is_staff', 'is_superuser'])
            gu, _ = GiteaUser.objects.get_or_create(
                user=user,
                defaults={'gitea_id': 99980 + i, 'username': uname, 'email': email},
            )
            self.gitea_users[uname] = gu

        self.stdout.write(f'  Users: {", ".join(self.gitea_users)}')
        if allow_password:
            self.stdout.write(self.style.WARNING(
                '  Web app  : http://localhost:5173/login -> "Dev Login" button.\n'
                '             No password: the button appears only on localhost/127.0.0.1\n'
                '             (not a LAN IP) and logs you in as devuser.\n'
                f'  Admin    : http://localhost:8001/admin/ -> paperauthor / {DEMO_PASSWORD}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '  Not a development settings module -- no password set on the demo users.'
            ))

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

        # The real spellings used across the paper's metadata.yml files.
        tag_defs = [
            ('tool', ['Autopsy', 'PECmd', 'LECmd', 'lnkinfo', 'ExifTool', 'Nautilus',
                      'Dolphin', 'gio', 'trash-put', 'kioclient5']),
            ('artifact', ['Trash', 'recently-used.xbel', 'Prefetch', 'LNK', 'WebHistory']),
            ('goal', ['tool-test', 'artifact-research', 'artifact-regression',
                      'cross-tool-validation', 'tool-regression']),
            ('platform', ['Linux', 'Windows']),
        ]
        self.tags = {}
        for scope_name, values in tag_defs:
            for val in values:
                # Tag.save() derives `name` from scope + value; pass value + scope only.
                tag, _ = Tag.objects.get_or_create(scope=self.scopes[scope_name], value=val)
                self.tags[tag.name] = tag

        for val in ('regression', 'defect-pin', 'absent-artifact', 'solr4', 'solr8',
                    'xdg', 'xbel', 'prefetch'):
            tag, _ = Tag.objects.get_or_create(scope=None, value=val)
            self.tags[tag.name] = tag

        self.stdout.write(f'  Tags: {len(self.tags)}')

    # ── OsInfo ──────────────────────────────────────────────────────────
    def _create_os_infos(self):
        # Recent Environments renders "{distribution} {version}" as its subtitle, so
        # these strings are visible in the screenshot.
        os_defs = [
            ('Linux', 'Ubuntu', '18.04'),
            ('Linux', 'Ubuntu', '20.04'),
            ('Linux', 'Ubuntu', '22.04'),
            ('Linux', 'Ubuntu', '24.04'),
            ('Linux', 'Kubuntu', '20.04'),
            ('Linux', 'Kubuntu', '22.04'),
            ('Linux', 'Kubuntu', '24.04'),
            ('Linux', 'Fedora', '41'),
            ('Linux', 'Fedora', '42'),
            ('Windows', 'Windows', '11 23H2'),
        ]
        self.os_infos = {}
        for os_name, dist, ver in os_defs:
            oi, _ = OsInfo.objects.get_or_create(
                os=os_name, distribution=dist, version=ver,
                defaults={'language': 'en_US', 'architecture': 'x86_64'},
            )
            self.os_infos[f'{dist}-{ver}'] = oi
        self.stdout.write(f'  OsInfos: {len(self.os_infos)}')

    # ── PostSetupInstallations ──────────────────────────────────────────
    def _create_installations(self):
        inst_defs = [
            ('autopsy-4.x', 'Per-version Autopsy MSI under C:\\Program Files\\Autopsy-<v>',
             'powershell -File C:\\adare\\Install-Autopsy.ps1'),
            ('solr4', 'Autopsy-embedded Apache Solr 4.10.3', 'powershell -File C:\\adare\\Setup-Solr4.ps1'),
            ('solr8', 'Autopsy-embedded Apache Solr 8.6.3+', 'powershell -File C:\\adare\\Setup-Solr8.ps1'),
            ('eztools', 'Eric Zimmerman tools (PECmd, LECmd) into the shared tools directory',
             'powershell -File C:\\adare\\Get-EZTools.ps1'),
            ('liblnk-utils', 'liblnk-utils 20181227 (lnkinfo)', 'apt install -y liblnk-utils'),
            ('libimage-exiftool-perl', 'ExifTool 12.76', 'apt install -y libimage-exiftool-perl'),
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
        gu = self.gitea_users['paperauthor']
        self.environments = {}
        for name, desc, os_key, days_ago, tag_names, inst_names in ENV_DEFS:
            ts = self.now - timedelta(days=days_ago, hours=3)
            env, created = Environment.objects.get_or_create(
                sha256hash=_hash('env', name),
                defaults={
                    'name': name,
                    'vm': f'/media/adare/AdareVMs/{name}.qcow2',
                    'vagrantbox': '',
                    'description': desc,
                    'os_info': self.os_infos[os_key],
                    'file': f'{GITEA_BASE}/environments/raw/branch/main/{name}.yml',
                    'published_by': gu,
                    'created_by': gu,
                    'published_at': ts,
                    'created_at': ts,
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
        gu = self.gitea_users['paperauthor']
        tfs_defs = [
            ('xdg-trash-checks', 'XDG trash can artifact assertions (paper 5.1)',
             [('standard.file_exists', 'FileExists', 'Assert a file exists'),
              ('standard.file_not_exists', 'FileNotExists', 'Assert a file does not exist'),
              ('trash.info_exists', 'TrashInfoExists', 'Assert a .trashinfo entry exists'),
              ('trash.files_entry_exists', 'TrashFilesEntryExists',
               'Assert the trashed payload exists under Trash/files')],
             ['goal:artifact-research', 'xdg']),
            ('xbel-checks', 'recently-used.xbel assertions (paper 5.2)',
             [('xbel.entry_exists', 'XbelEntryExists', 'Assert an XBEL bookmark entry exists'),
              ('xbel.timestamp_precision', 'XbelTimestampPrecision',
               'Assert an XBEL timestamp value and its precision')],
             ['goal:artifact-regression', 'xbel']),
            ('excel-report-checks', 'Autopsy Excel report comparison (paper 5.4)',
             [('excel.validate_columns', 'ExcelValidateColumns',
               'Assert a sheet carries the expected column headers'),
              ('excel.column_contains', 'ExcelColumnContains',
               'Assert a sheet column contains an expected value')],
             ['goal:tool-regression', 'regression']),
            ('tool-output-checks', 'CLI forensic tool output assertions (paper 5.3, 5.5)',
             [('prefetch.field_matches', 'PrefetchFieldMatches',
               'Assert a PECmd prefetch field value'),
              ('lnk.field_matches', 'LnkFieldMatches', 'Assert a parsed LNK field value'),
              ('json.key_matches', 'JsonKeyMatches', 'Assert a JSON key value')],
             ['goal:tool-test']),
        ]
        self.tfs = {}
        self.testfunctions = {}
        for tfs_name, desc, funcs, tag_names in tfs_defs:
            tfs, created = TestfunctionSet.objects.get_or_create(
                sha256hash=_hash('tfs', tfs_name),
                defaults={
                    'name': tfs_name,
                    'description': desc,
                    'file': f'{GITEA_BASE}/testfunctions/raw/branch/main/{tfs_name}.py',
                    'requirements_file': f'{GITEA_BASE}/testfunctions/raw/branch/main/{tfs_name}-req.txt',
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
        self.stdout.write(
            f'  TestfunctionSets: {len(self.tfs)}, TestFunctions: {len(self.testfunctions)}'
        )

    # ── Tools + TestParameters ──────────────────────────────────────────
    def _create_tools_and_params(self):
        tool_defs = [
            ('Autopsy', 'autopsy64.exe'),
            ('PECmd', 'PECmd.exe'),
            ('LECmd', 'LECmd.exe'),
            ('lnkinfo', 'lnkinfo'),
            ('ExifTool', 'exiftool'),
        ]
        self.tools = {}
        for name, cmd in tool_defs:
            tool, _ = Tool.objects.get_or_create(name=name, defaults={'command': cmd})
            self.tools[name] = tool

        param_defs = [
            ('dst', 'string', 'Path to the artifact under test'),
            ('key', 'string', 'Field, column, sheet or XPath selector'),
            ('expected', 'string', 'Expected value'),
            ('precision', 'string', 'Required timestamp precision'),
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
        home = '/home/adare'
        at_defs = [
            ('trash_info_exists', 'A .trashinfo entry names the deleted file',
             'trash.info_exists', None,
             [('dst', f'{home}/.local/share/Trash/info/report.txt.trashinfo')]),
            ('trash_files_entry_exists', 'The trashed payload is under Trash/files',
             'trash.files_entry_exists', None,
             [('dst', f'{home}/.local/share/Trash/files/report.txt')]),
            ('trash_original_absent', 'The original path is gone after deletion',
             'standard.file_not_exists', None, [('dst', f'{home}/Documents/report.txt')]),
            ('xbel_exists', 'recently-used.xbel was created by the interaction',
             'standard.file_exists', None,
             [('dst', f'{home}/.local/share/recently-used.xbel')]),
            ('xbel_absent_after_open', 'recently-used.xbel is absent after the interaction',
             'standard.file_not_exists', None,
             [('dst', f'{home}/.local/share/recently-used.xbel')]),
            ('xbel_bookmark_href', 'The single bookmark names the opened document',
             'xbel.entry_exists', None,
             [('key', '//bookmark/@href'),
              ('expected', f'file://{home}/Documents/textfile.txt')]),
            ('xbel_visited_is_epoch_minus_one',
             "Defect pin: 'visited' is the integer -1 sentinel (GLib < 2.66)",
             'xbel.timestamp_precision', None,
             [('key', '//bookmark/@visited'), ('expected', '1969-12-31T23:59:59Z'),
              ('precision', 'second')]),
            ('xbel_visited_subsecond_precision',
             "'visited' carries sub-second precision (GLib >= 2.66)",
             'xbel.timestamp_precision', None,
             [('key', '//bookmark/@visited'), ('precision', 'microsecond')]),
            ('prefetch_run_count', 'PECmd reports ten regedit executions',
             'prefetch.field_matches', 'PECmd',
             [('key', 'RunCount'), ('expected', '10')]),
            ('autopsy_webhistory_columns',
             'The Web History sheet carries the 4.4.0 baseline column headers',
             'excel.validate_columns', 'Autopsy',
             [('key', 'Web History'),
              ('expected', 'URL,Date Accessed,Referrer,Title,Program Name,Domain,Source File')]),
            ('autopsy_webhistory_rows',
             'The Web History sheet rows match the 4.4.0 reference workbook',
             'excel.column_contains', 'Autopsy',
             [('key', 'Web History'), ('expected', 'mozilla.org')]),
            ('lnk_local_path', 'The parser recovered the LNK local path',
             'lnk.field_matches', None,
             [('key', 'LocalPath'), ('expected', 'C:\\Windows\\System32\\calc.exe')]),
            ('lnk_exit_code_zero', 'The parser exited zero on the sample',
             'json.key_matches', None, [('key', 'ExitCode'), ('expected', '0')]),
        ]
        self.abstract_tests = {}
        for at_name, desc, tf_name, tool_name, params in at_defs:
            entries = []
            for pname, pval in params:
                entry, _ = TestParameterEntry.objects.get_or_create(
                    parameter=self.params[pname], value=pval,
                )
                entries.append(entry)

            at, created = AbstractTest.objects.get_or_create(
                name=at_name, testfunction=self.testfunctions[tf_name],
                defaults={'description': desc},
            )
            if created:
                at.parameters.set(entries)
                if tool_name:
                    at.tools.add(self.tools[tool_name])
            self.abstract_tests[at_name] = at
        self.stdout.write(f'  AbstractTests: {len(self.abstract_tests)}')

    # ── Experiments ─────────────────────────────────────────────────────
    def _experiment_defs(self):
        """(name, description, tags, environments, abstract_tests, user, days_ago, hours_ago)."""
        defs = []

        # §5.1 Explorative artifact research -- the Linux trash can.
        for name, tool_tag, envs, days_ago, desc in DELETION_DEFS:
            tags = [tool_tag, 'artifact:Trash', 'goal:artifact-research', 'platform:Linux', 'xdg']
            defs.append((name, desc, tags, envs, TRASH_TESTS, 'paperauthor', days_ago, 0))

        # §5.2 Artifact regression testing -- recently-used.xbel.
        for env, days_ago, fm_tag, extra, tests, _status, _detail, desc in XBEL_DEFS:
            tags = [fm_tag, 'artifact:recently-used.xbel', 'goal:artifact-regression',
                    'platform:Linux', 'regression', 'xdg', 'xbel'] + extra
            defs.append((f'open-single-text-file-{env}', desc, tags, [env], tests,
                         'paperauthor', days_ago, 0))

        # §5.3 Tool validation of PECmd.
        defs.append((
            PECMD_NAME, PECMD_DESC,
            ['tool:PECmd', 'artifact:Prefetch', 'goal:tool-test', 'platform:Windows', 'prefetch'],
            ['win11'], ['prefetch_run_count'], 'reviewer1', 3, 0,
        ))

        # §5.4 Autopsy tool regression testing -- generated from the version lists so the
        # 24 rows stay in lockstep with provisioning/versions_solr{4,8}.txt.
        autopsy_tests = ['autopsy_webhistory_columns', 'autopsy_webhistory_rows']
        versions = [(v, 'win11-autopsy-solr4', 'solr4', '4.10.3') for v in AUTOPSY_SOLR4]
        versions += [(v, 'win11-autopsy-solr8', 'solr8', '8.6.3+') for v in AUTOPSY_SOLR8]
        for i, (version, env, solr_tag, solr_version) in enumerate(versions):
            desc = (
                f'Autopsy {version} regression test (paper section 5.4): run the Recent '
                'Activity ingest module over the NIST CFReDS Windows image, export the Excel '
                'report, and compare every sheet against the 4.4.0 baseline. Autopsy '
                f'{version} bundles Solr {solr_version}.'
            )
            tags = ['tool:Autopsy', 'artifact:WebHistory', 'goal:tool-regression',
                    'platform:Windows', 'regression', solr_tag]
            # Older than everything else so they do not crowd out Recent Experiments.
            defs.append((autopsy_experiment_name(version), desc, tags, [env], autopsy_tests,
                         'reviewer1', 30 + i * 2, 0))

        # §5.5 Cross-tool validation -- three LNK parsers.
        for i, (name, env, tool_tag, plat_tag, days_ago, _st, _detail, desc) in enumerate(LNK_DEFS):
            tags = [tool_tag, 'artifact:LNK', 'goal:cross-tool-validation', 'goal:tool-test',
                    plat_tag]
            defs.append((name, desc, tags, [env], ['lnk_local_path', 'lnk_exit_code_zero'],
                         'paperauthor', days_ago, 2 + i * 3))

        return defs

    def _create_experiments(self):
        gu = self.gitea_users
        self.experiments = {}
        for (name, desc, tag_names, env_names, test_names, user_key,
             days_ago, hours_ago) in self._experiment_defs():
            ts = self.now - timedelta(days=days_ago, hours=hours_ago)
            exp, created = Experiment.objects.get_or_create(
                sha256hash=_hash('exp', name),
                defaults={
                    'name': name,
                    'description': desc,
                    'playbook_file': f'{GITEA_BASE}/experiments/raw/branch/main/{name}/playbook.yml',
                    'metadata_file': f'{GITEA_BASE}/experiments/raw/branch/main/{name}/metadata.yml',
                    'sha256playbook': _hash('exp-playbook', name),
                    'published_by': gu[user_key],
                    'created_by': gu[user_key],
                    'published_at': ts,
                    'created_at': ts,
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
    def _run_defs(self):
        """(experiment, environment, days_ago, run_status, result_status, detail)."""
        defs = []

        # §5.1 -- one run per (experiment, environment) pair the playbook actually names,
        # plus a repeat run for the three broadest deletion paths (explorative research
        # revisits them), which is what brings the section to the paper's 42 runs.
        trash_detail = (
            'XDG trash can artifacts created as expected: .trashinfo entry written, payload '
            'moved under Trash/files, original path removed.'
        )
        repeat = {'deletefile_gio_trash', 'deletefile_trashput', 'deletefile_nautilus_by_click'}
        for name, _tool_tag, envs, days_ago, _desc in DELETION_DEFS:
            # Runs walk forward from the experiment's publication date, never before it.
            for i, env in enumerate(envs):
                defs.append((name, env, days_ago - i, 'finished', 'success', trash_detail))
            if name in repeat:
                for i, env in enumerate(envs):
                    defs.append((name, env, max(days_ago - 8, 1) + i, 'finished', 'success',
                                 trash_detail))

        # §5.2 -- the paper's actual findings drive result_status.
        for env, days_ago, _fm, _extra, _tests, result_status, detail, _desc in XBEL_DEFS:
            defs.append((f'open-single-text-file-{env}', env, days_ago, 'finished',
                         result_status, detail))

        # §5.3
        defs.append((PECMD_NAME, 'win11', 3, 'finished', 'success',
                     'PECmd reported RunCount 10 and the expected last-run timestamp after '
                     'each of the ten regedit executions.'))

        # §5.4 -- 4.4.0 is the baseline the expectation was defined from; 4.22.1 warns.
        versions = [(v, 'win11-autopsy-solr4') for v in AUTOPSY_SOLR4]
        versions += [(v, 'win11-autopsy-solr8') for v in AUTOPSY_SOLR8]
        for i, (version, env) in enumerate(versions):
            if version == '4.4.0':
                result_status = 'success'
                detail = ('Baseline: the Web History sheet defines the expected columns and '
                          'rows for every later version.')
            elif version == '4.22.1':
                result_status = 'warning'
                detail = AUTOPSY_WARNING
            else:
                result_status = 'success'
                detail = 'Web History sheet columns and rows match the 4.4.0 reference workbook.'
            defs.append((autopsy_experiment_name(version), env, 30 + i * 2, 'finished',
                         result_status, detail))

        # §5.5
        for name, env, _tool, _plat, days_ago, result_status, detail, _desc in LNK_DEFS:
            defs.append((name, env, days_ago, 'finished', result_status, detail))

        # Two live states so the run list is not uniformly finished.
        defs.append(('lnk_lnkinfo_ubuntu2404', 'ubuntu24043', 0, 'running', 'none',
                     'Re-running against liblnk 20240423 to re-baseline the L2/L3 rejection.'))
        defs.append(('autopsy_4.22.1_webhistory', 'win11-autopsy-solr8', 0, 'pending', 'none',
                     'Queued: re-run with the action descriptions indented under their action keys.'))

        return defs

    def _create_runs_and_events(self):
        status_map = {s.name: s for s in Status.objects.all()}
        gu = self.gitea_users['paperauthor']
        run_defs = self._run_defs()

        # Idempotency: a (experiment, environment) pair is seeded only until it holds as
        # many runs as this seeder declares for it.
        expected_counts = Counter((e, v) for e, v, *_ in run_defs)

        created = 0
        for exp_name, env_name, days_ago, run_status, result_status, detail in run_defs:
            exp = self.experiments[exp_name]
            env = self.environments[env_name]

            # `existing` includes rows created earlier in this same loop, so a pair
            # declared twice is filled twice on a fresh DB and skipped on a re-seed.
            existing = ExperimentRun.objects.filter(experiment=exp, environment=env).count()
            if existing >= expected_counts[(exp_name, env_name)]:
                continue

            ts_start = self.now - timedelta(days=days_ago, hours=1)
            ts_end = ts_start + timedelta(minutes=22)

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
            # Only the adarevm log: attaching all four would litter MEDIA_ROOT with
            # ~240 stub files for a home-page screenshot.
            run.adarevm_logfile.save(
                f'{exp_name}-{env_name}-adarevm.log',
                ContentFile(self._logfile_body(exp_name, env_name, run_status, detail)),
                save=False,
            )
            run.save()
            created += 1

            if run_status == 'finished':
                self._create_events_for_run(run, result_status, exp_name, env_name,
                                            detail, status_map)

        total = ExperimentRun.objects.filter(
            experiment__sha256hash__in=[_hash('exp', n) for n in paper_experiment_names()]
        ).count()
        self.stdout.write(f'  ExperimentRuns: {created} created, {total} total')

    def _logfile_body(self, exp_name, env_name, run_status, detail):
        lines = [f'adarevm: session start ({env_name})', f'adarevm: playbook {exp_name}',
                 'adarevm: testfunction discovery complete (cached)']
        if run_status == 'finished':
            lines += [f'adarevm: result -- {detail}', 'adarevm: session end']
        else:
            lines.append(f'adarevm: {run_status}')
        return ('\n'.join(lines) + '\n').encode()

    def _create_events_for_run(self, run, result_status, exp_name, env_name, detail, status_map):
        ts = run.timestamp_start + timedelta(minutes=1)

        if not ActionEvent.objects.filter(run=run, event_group_id='0').exists():
            ActionEvent.objects.create(
                run=run, event_group_id='0', timestamp=ts,
                category='command', status=status_map['finished'],
                action_type='command', action_id='setup-environment',
                action_data=json.dumps({
                    'command': f'adare vm start {env_name}',
                    'returncode': 0,
                    'stdout': f'{env_name}: guest agent responding, screen 1920x1080.',
                }),
                success=True,
            )

        ts += timedelta(minutes=3)
        if not ActionEvent.objects.filter(run=run, event_group_id='1').exists():
            ActionEvent.objects.create(
                run=run, event_group_id='1', timestamp=ts,
                category='command', status=status_map['finished'],
                action_type='command', action_id='run-playbook',
                action_data=json.dumps({
                    'command': f'adare experiment run {exp_name} --environment {env_name}',
                    'returncode': 0 if result_status == 'success' else 1,
                    'stdout': detail,
                }),
                success=(result_status == 'success'),
            )

        group, ts = 2, ts + timedelta(minutes=2)
        for at in run.experiment.abstract_tests.all():
            if TestEvent.objects.filter(run=run, abstracttest=at).exists():
                continue
            test_status = status_map[result_status]
            result = Result.objects.create(
                status=test_status, details=f'{at.name}: {detail}',
            )
            TestEvent.objects.create(
                run=run, event_group_id=str(group), timestamp=ts,
                category='test', status=test_status,
                abstracttest=at, result=result,
                success=(result_status == 'success'),
            )
            group += 1
            ts += timedelta(seconds=45)

        if result_status == 'failed' and not ErrorEvent.objects.filter(run=run).exists():
            ErrorEvent.objects.create(
                run=run, event_group_id=str(group), timestamp=ts,
                category='error', status=status_map['error'],
                error_name='AssertionError',
                error_msg=detail[:2000],
                success=False,
            )
            group += 1

        if exp_name not in CLI_EXPERIMENTS:
            ts += timedelta(seconds=10)
            if not ActionEvent.objects.filter(run=run, action_type='find').exists():
                ActionEvent.objects.create(
                    run=run, event_group_id=str(group), timestamp=ts,
                    category='action', status=status_map['finished'],
                    action_type='find', action_id='find-file-manager',
                    action_data=json.dumps({
                        'objective': 'Locate the file manager window',
                        'positions': '412,286',
                    }),
                    success=True,
                )
                group += 1
            ts += timedelta(seconds=5)
            if not ActionEvent.objects.filter(run=run, action_type='click').exists():
                ActionEvent.objects.create(
                    run=run, event_group_id=str(group), timestamp=ts,
                    category='action', status=status_map['finished'],
                    action_type='click', action_id='click-target',
                    action_data=json.dumps({'target': 'Documents', 'clicktype': 'double'}),
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
        exps, envs = self.experiments, self.environments

        # (title, action, ct, obj, is_modify, pr_status, pr_number, labels, requester, days_ago)
        req_defs = [
            ('Add lnk_lnkinfo_ubuntu2404 experiment', 'create', exp_ct,
             exps['lnk_lnkinfo_ubuntu2404'], False, 'open', 201, ['enhancement'],
             'paperauthor', 1),
            ('Pin recently-used.xbel defect on Ubuntu 20.04', 'modify', exp_ct,
             exps['open-single-text-file-ubuntu-2004'], True, 'open', 202,
             ['bug', 'review-needed'], 'paperauthor', 6),
            ('Add win11-autopsy-solr8 environment', 'create', env_ct,
             envs['win11-autopsy-solr8'], False, 'closed', 203, ['enhancement'],
             'paperauthor', 2),
            ('Indent the 352 dropped action descriptions in the Autopsy playbooks', 'modify',
             exp_ct, exps['autopsy_4.22.1_webhistory'], True, 'open', 204, ['bug', 'urgent'],
             'reviewer1', 3),
            ('Add pecmd tool-validation experiment', 'create', exp_ct, exps[PECMD_NAME],
             False, 'closed', 205, ['enhancement'], 'reviewer1', 4),
            ('Assert absent recently-used.xbel on Kubuntu 22.04', 'create', exp_ct,
             exps['open-single-text-file-kubuntu-2204'], False, 'closed', 206,
             ['enhancement', 'review-needed'], 'paperauthor', 8),
        ]

        count = 0
        for (title, action, obj_ct, obj, is_modify, pr_status, pr_num,
             label_names, requester, days_ago) in req_defs:
            if Request.objects.filter(gitea_pr_number=pr_num).exists():
                count += 1
                continue
            creation = self.now - timedelta(days=days_ago)
            req = Request.objects.create(
                title=title,
                description=f'Paper case-study demo request: {title}',
                creation_date=creation,
                last_change_date=creation + timedelta(hours=2),
                gitea_pr_url=f'{GITEA_BASE}/experiments/pulls/{pr_num}',
                gitea_pr_number=pr_num,
                gitea_pr_status=pr_status,
                action=action,
                objective_name=obj._meta.model_name,
                objective=obj_ct,
                object_id=obj.pk,
                old_objective_name=obj._meta.model_name if is_modify else None,
                old_objective=obj_ct if is_modify else None,
                old_object_id=obj.pk if is_modify else None,
                requester=self.gitea_users[requester],
            )
            req.labels.set([labels[n] for n in label_names])
            count += 1
        self.stdout.write(f'  Requests: {count}')

    # ── Summary ─────────────────────────────────────────────────────────
    def _print_summary(self):
        exp_hashes = [_hash('exp', n) for n in paper_experiment_names()]
        env_hashes = [_hash('env', n) for n in paper_environment_names()]
        paper_exps = Experiment.objects.filter(sha256hash__in=exp_hashes)
        paper_envs = Environment.objects.filter(sha256hash__in=env_hashes)
        paper_runs = ExperimentRun.objects.filter(
            Q(experiment__in=paper_exps) | Q(environment__in=paper_envs)
        )
        self.stdout.write(self.style.SUCCESS(
            f'\nPaper demo data seeded (paper sections 5.1-5.5):\n'
            f'  {paper_exps.count()} experiments, '
            f'{paper_envs.count()} environments, '
            f'{paper_runs.count()} runs\n'
            f'  DB totals: {Experiment.objects.count()} experiments, '
            f'{Environment.objects.count()} environments, '
            f'{ExperimentRun.objects.count()} runs,\n'
            f'  {TestFunction.objects.count()} testfunctions, '
            f'{Request.objects.count()} requests, '
            f'{User.objects.count()} users'
        ))

    # ── Purge ───────────────────────────────────────────────────────────
    def _purge(self):
        """Delete only this seeder's rows, matched by its `paper-` hash namespace.

        FK-safe order: runs first (they CASCADE their events and PROTECT their
        environment), then experiments, then environments, then the demo requests.
        Shared Tag / OsInfo / Status / TestfunctionSet / Tool rows are left in place --
        they are harmless and may be shared with `seed_dev_data`.
        """
        exp_hashes = [_hash('exp', n) for n in paper_experiment_names()]
        env_hashes = [_hash('env', n) for n in paper_environment_names()]
        exps = Experiment.objects.filter(sha256hash__in=exp_hashes)
        envs = Environment.objects.filter(sha256hash__in=env_hashes)

        runs = ExperimentRun.objects.filter(Q(experiment__in=exps) | Q(environment__in=envs))
        run_count = runs.count()
        for run in runs.iterator():
            if run.adarevm_logfile:
                run.adarevm_logfile.delete(save=False)
        runs.delete()

        # Results are only referenced by TestEvent (PROTECT), so anything orphaned by the
        # cascade above is dead weight.
        orphan_results = Result.objects.filter(testevent__isnull=True)
        result_count = orphan_results.count()
        orphan_results.delete()

        req_count = Request.objects.filter(gitea_pr_number__in=PAPER_PR_NUMBERS).count()
        Request.objects.filter(gitea_pr_number__in=PAPER_PR_NUMBERS).delete()

        exp_count, env_count = exps.count(), envs.count()
        exps.delete()
        envs.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Paper demo data purged:\n'
            f'  {run_count} runs (and their events), '
            f'{result_count} orphaned results,\n'
            f'  {exp_count} experiments, {env_count} environments, {req_count} requests\n'
            f'  Left in place: tags, os infos, installations, testfunction sets, tools, users.\n'
            f'  DB totals now: {Experiment.objects.count()} experiments, '
            f'{Environment.objects.count()} environments, '
            f'{ExperimentRun.objects.count()} runs'
        ))

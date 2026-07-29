"""
Find merged/closed Gitea PRs whose ingest/finalize never landed in the DB.

The ingest/finalize endpoints (giteaeventmanager/views.py) are only ever hit by
the Gitea Actions pipeline running in the adareTEST repo, not by anything this
backend triggers itself. If that pipeline silently fails to call them (wrong
host, secret mismatch, ...), a merged PR just never shows up as a published
Experiment/Environment/TestfunctionSet — with no error anywhere. This command
compares Gitea's PR history against local Request/published state to find and
optionally backfill those gaps.
"""
import re

from django.conf import settings
from django.core.management.base import BaseCommand

import giteaapi as gitea

from giteaeventmanager.auth import GiteaAuthHandle
from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.service import TITLE_PATTERN, _PLUGINS, ingest_pr, finalize_pr
from experiments.models import Request


class Command(BaseCommand):
    help = 'Find (and optionally fix) merged Gitea PRs that never got ingested/finalized locally'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true',
                             help='Actually ingest/finalize the gaps found. Without this flag, only reports them.')
        parser.add_argument('--dry-run', action='store_true',
                             help='Report gaps only (the default; explicit flag for scripting).')

    def handle(self, *args, **options):
        fix = options['fix']

        conf = gitea.Configuration()
        conf.host = settings.GITEA_API
        conf.api_key['token'] = GiteaAuthHandle.get_token()
        api = gitea.ApiClient(conf)
        repo_api = gitea.RepositoryApi(api)

        owner = settings.GITEA_EXPERIMENTS_REPO_OWNER
        repo = settings.GITEA_EXPERIMENTS_REPO

        prs = repo_api.repo_list_pull_requests(owner=owner, repo=repo, state='closed')

        gaps = []
        for pr in prs:
            if not pr.merged:
                continue
            match = re.match(TITLE_PATTERN, pr.title)
            if not match:
                continue
            objective, _action, name = match.group('objective'), match.group('action'), match.group('name').strip()

            request = Request.objects.filter(gitea_pr_number=pr.number).first()
            if request is not None:
                if not getattr(request.object, 'published', False):
                    gaps.append({'pr': pr, 'kind': 'never_finalized', 'request': request})
                continue

            # no Request row: either finalize already ran successfully (it deletes
            # the Request on publish, which is the expected happy path), or ingest
            # never got a Request created in the first place. Tell those apart by
            # checking whether a published object with this name exists.
            plugin_class = _PLUGINS.get(objective)
            published_object = None
            if plugin_class is not None:
                published_object = plugin_class(objective=objective, object_name=name, last_commit='').get_object()
            if published_object is None or not getattr(published_object, 'published', False):
                gaps.append({'pr': pr, 'kind': 'never_ingested'})

        if not gaps:
            self.stdout.write(self.style.SUCCESS('no gaps found — every merged PR is published'))
            return

        self.stdout.write(f'found {len(gaps)} gap(s):')
        for gap in gaps:
            pr = gap['pr']
            self.stdout.write(f'  PR #{pr.number} "{pr.title}" ({gap["kind"]})')

        if not fix:
            self.stdout.write(self.style.WARNING('\ndry-run: pass --fix to ingest/finalize these PRs'))
            return

        for gap in gaps:
            pr = gap['pr']
            try:
                if gap['kind'] == 'never_ingested':
                    ingest_pr(pr.number)
                result = finalize_pr(pr.number)
            except TaskFailure as e:
                self.stdout.write(self.style.ERROR(f'  PR #{pr.number}: {e}'))
                continue
            self.stdout.write(self.style.SUCCESS(f'  PR #{pr.number}: {result}'))

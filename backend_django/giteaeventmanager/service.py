"""
Synchronous ingest/finalize services for Gitea pull requests.

These are the single, event-driven bridge between Gitea PRs and the backend,
reached by two triggers:

* client inline submit (direct in-process call at PR-open time), and
* the Actions pipeline (via the ingest/finalize HTTP endpoints).

Both paths run the same idempotent logic synchronously (no Celery, no polling),
returning a real pass/fail result. The heavy lifting (download/hash/parse/persist)
reuses the plugins in ``action/plugin.py`` and the handlers in ``action/base.py``.
"""
import re
import logging

import requests
from helperfunctions.http import HTTP_TIMEOUT
from django.conf import settings

from giteaeventmanager.auth import GiteaAuthHandle
from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.errorcodes import SubmitErrorCode
from giteaeventmanager.action.base import PRIngestCreate, PRIngestModify, PRIngestRemove, PRFinalize, find_owning_request
from giteaeventmanager.action.plugin import (
    TestfunctionsetPlugin,
    ExperimentPlugin,
    EnvironmentPlugin,
)

log = logging.getLogger(__name__)

# PR titles are in the form "[<objective> <action>] <name>", e.g. "[experiment create] ubuntu_deletefile"
TITLE_PATTERN = r"\[(?P<objective>\w+) (?P<action>\w+)\] (?P<name>.+)"

_PLUGINS = {
    "experiment": ExperimentPlugin,
    "testfunction": TestfunctionsetPlugin,
    "environment": EnvironmentPlugin,
}

# ingest handler per PR action; finalize is always PRFinalize (it dispatches internally)
_INGEST_HANDLERS = {
    "create": PRIngestCreate,
    "modify": PRIngestModify,
    "remove": PRIngestRemove,
}


def _fetch_pull_request(prnumber: int) -> dict:
    """Fetch the raw Gitea pull request object (head SHA, title, state, merge info)."""
    token = GiteaAuthHandle.get_token()
    url = f'{settings.GITEA_REPO_API}pulls/{prnumber}'
    response = requests.get(url, headers={'Authorization': f'token {token}'}, timeout=HTTP_TIMEOUT)
    if response.status_code != 200:
        raise TaskFailure(f'could not fetch pull request {prnumber} ({response.status_code}): {response.text}',
                          code=SubmitErrorCode.UPSTREAM_UNAVAILABLE)
    return response.json()


def _parse_title(title: str) -> tuple[str, str, str]:
    match = re.match(TITLE_PATTERN, title)
    if not match:
        raise TaskFailure(f'could not parse pull request title: {title}',
                          code=SubmitErrorCode.PARSE_ERROR)
    return match.group("objective"), match.group("action"), match.group("name").strip()


def _plugin_for(objective: str, object_name: str, last_commit: str):
    plugin_class = _PLUGINS.get(objective)
    if not plugin_class:
        raise TaskFailure(f'unknown objective "{objective}"', code=SubmitErrorCode.PARSE_ERROR)
    return plugin_class(objective=objective, object_name=object_name, last_commit=last_commit)


def _build_json_data(pr: dict, action: str) -> dict:
    """Wrap a Gitea PR object in the webhook-shaped payload the action handlers expect."""
    return {"action": action, "number": pr["number"], "pull_request": pr}


def _ingest_result(objective: str, object_instance) -> dict:
    if objective == "experiment":
        return {
            "experiment_ulid": object_instance.ulid,
            "playbook_file": object_instance.playbook_file,
            "sha256playbook": object_instance.sha256playbook,
            "tests": [
                {"name": test.name, "type": test.testfunction.type}
                for test in object_instance.abstract_tests.all()
            ],
        }
    # generic payload for testfunction / environment objects
    return {
        "object_ulid": object_instance.ulid,
        "name": object_instance.name,
        "sha256hash": object_instance.sha256hash,
    }


def ingest_pr(prnumber: int) -> dict:
    """Ingest a PR into a draft object (``published=False``). Idempotent upsert.

    Raises ``TaskFailure`` with a concrete message on any problem (unknown
    environment/testfunction, malformed metadata, missing files, duplicate, ...).
    """
    pr = _fetch_pull_request(prnumber)
    objective, action, object_name = _parse_title(pr["title"])
    handler_cls = _INGEST_HANDLERS.get(action)
    if not handler_cls:
        raise TaskFailure(f'ingest does not support the "{action}" action',
                          code=SubmitErrorCode.PARSE_ERROR)

    plugin = _plugin_for(objective, object_name, pr["head"]["sha"])
    handler = handler_cls(plugin, _build_json_data(pr, "opened"), objective, action, object_name)
    try:
        handler.check()
        handler.action()
        result = _ingest_result(objective, handler.request.object)
    finally:
        # always remove downloaded files, including on the error path
        plugin.cleanup()
    log.info(f'ingested pull request {prnumber} ({objective} {object_name})')
    return result


def classify_submission(entity_type: str, name: str) -> dict:
    """Pre-submit, name-based classification of a *create* submission.

    Purely local (no Gitea write, no file download): content/hash checks need the
    files in Gitea and are left to ``ingest_pr``. Lets the interactive surfaces
    (CLI, React) warn *before* opening a PR — avoiding the create-then-auto-close
    churn Layer B performs when a terminal duplicate still reaches ingest.

    Returns ``{code, message, pr_number?}`` where ``code`` is a ``SubmitErrorCode``:

    * an object with this name is already published -> ``ALREADY_PUBLISHED``
    * an unpublished draft owned by an open Request -> ``OPEN_DUPLICATE`` (+ ``pr_number``)
    * otherwise -> ``OK``
    """
    plugin_class = _PLUGINS.get(entity_type)
    if not plugin_class:
        raise TaskFailure(f'unknown objective "{entity_type}"', code=SubmitErrorCode.PARSE_ERROR)

    plugin = plugin_class(objective=entity_type, object_name=name, last_commit='')
    existing = plugin.get_object()  # published-aware name lookup
    if existing is None:
        return {"code": SubmitErrorCode.OK, "message": ""}

    if getattr(existing, 'published', False):
        return {
            "code": SubmitErrorCode.ALREADY_PUBLISHED,
            "message": f'{name} is already published — submit a modify PR instead of a create.',
        }

    owning_request = find_owning_request(existing)
    if owning_request is not None:
        return {
            "code": SubmitErrorCode.OPEN_DUPLICATE,
            "pr_number": owning_request.gitea_pr_number,
            "message": (f'{name} is already proposed by open pull request '
                        f'#{owning_request.gitea_pr_number}; update that PR instead of opening a new one.'),
        }

    # unpublished draft with no owning request -> a stale orphan; a fresh create
    # will reconcile it away on ingest, so nothing to warn about here.
    return {"code": SubmitErrorCode.OK, "message": ""}


def finalize_pr(prnumber: int) -> dict:
    """Finalize a closed PR: publish on merge, delete the draft on non-merge close."""
    pr = _fetch_pull_request(prnumber)
    objective, action, object_name = _parse_title(pr["title"])

    plugin = _plugin_for(objective, object_name, pr["head"]["sha"])
    handler = PRFinalize(plugin, _build_json_data(pr, "closed"), objective, action, object_name)
    handler.check()
    result = handler.action()
    result = {"prnumber": prnumber, **result}
    log.info(f'finalized pull request {prnumber} ({objective} {object_name}): {result}')
    return result

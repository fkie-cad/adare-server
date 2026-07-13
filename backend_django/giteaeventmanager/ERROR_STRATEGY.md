# Submit / ingest error strategy

Every submit/ingest failure is tagged with a machine-readable
`SubmitErrorCode` (`giteaeventmanager/errorcodes.py`) and surfaced in the 400
body (`{"error": <msg>, "code": <CODE>}`). The code — not the message string —
drives what happens on each surface.

## Decision matrix

| Code | Trigger | Interactive (CLI / React) | Async (pipeline / server) | Auto-close? |
|---|---|---|---|---|
| `ALREADY_PUBLISHED` | create for a name already published | prompt "already published — submit a modify PR instead?" | close create PR + explanatory comment | **Yes** |
| `OPEN_DUPLICATE` | draft name owned by another open PR #M | reuse / point at #M | close the *newer* PR + comment (never #M) | **Yes** |
| `CONTENT_DUPLICATE` | same content hash, different object | inform | leave open | No |
| `INVALID_CONTENT` | schema / playbook / postsetup / requirements / malformed remove | show precise message; fix files & re-push | leave open | No |
| `MISSING_FILES` | expected files absent on the branch | show message | leave open | No |
| `UNKNOWN_DEPENDENCY` | env / testfunction / vagrantbox referenced but absent | show message + "publish the dependency first" | leave open | No |
| `NOT_FOUND` | modify/remove for a name that does not exist | show message | leave open | No |
| `INVALID_STATE` | modify/remove of an unpublished draft | show message | leave open | No |
| `UPSTREAM_UNAVAILABLE` / `PARSE_ERROR` | Gitea/Vagrant Cloud unreachable, title unparseable | transient; retry | fail job for re-run; never close | No |

**Principle:** terminal wrong-ops (published / open-duplicate) are auto-closed;
fixable submissions stay open so the user iterates on the same PR;
transient/infra failures are retried and never closed.

## Where each capability lives

- **Codes** are raised in `action/base.py`, `action/plugin.py`, `service.py`.
- **Auto-close** is `PRIngestCreate._auto_close_terminal_duplicate` →
  `helperfunctions/gitea_write.py` (`comment_on_pull_request` + `close_pull_request`,
  using the `write:repository` token). Flag-guarded by
  `AUTO_CLOSE_TERMINAL_DUPLICATES` (default on). Best-effort: a Gitea write
  failure still yields the clean coded 400, never a 500. Closing emits a
  `closed` event that routes to `finalize` (a no-op with no draft) — no loop.
- **Pre-submit classification** is `service.classify_submission` (name-based, no
  Gitea write), exposed at `POST /api/submit/precheck/` (`IsAuthenticated`,
  registered mode-independently). The CLI and React proxy call it *before*
  opening a create PR so a terminal duplicate is guided rather than turned into
  a PR the async path would immediately auto-close.

## Pipeline (Actions) note

The Actions workflow that drives the async path lives in the **external
`adareTEST` repo** (not in this repo). It calls `POST /internal/gitea/ingest/`
on open/synchronize and `/internal/gitea/finalize/` on close. **No workflow
change is required for auto-close**: Layer B runs inside `ingest_pr`, so it
covers the pipeline path (and any stray duplicate) uniformly. A future nicety is
surfacing the returned `code` in the failing CI job for a clearer message.

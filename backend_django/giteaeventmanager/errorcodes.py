"""Machine-readable error codes for the submit/ingest pipeline.

Every ``TaskFailure`` raised on the ingest/finalize/classify path carries one of
these codes so the interactive surfaces (CLI, React) and the async surfaces
(Actions pipeline, server auto-close) can decide *what happens* without parsing
the human message. The decision matrix (interactive guidance vs. async
auto-close) is documented in ``docs`` and keyed on these constants.

Principle:
  * terminal wrong-ops (``ALREADY_PUBLISHED``, ``OPEN_DUPLICATE``) -> auto-closed
  * fixable submissions (``INVALID_CONTENT``, ``MISSING_FILES``,
    ``UNKNOWN_DEPENDENCY``, ``CONTENT_DUPLICATE``, ``NOT_FOUND``,
    ``INVALID_STATE``) -> left open so the user iterates on the same PR
  * transient/infra (``UPSTREAM_UNAVAILABLE``, ``PARSE_ERROR``) -> retried,
    never closed
"""


class SubmitErrorCode:
    # non-error sentinel returned by classify_submission()
    OK = "OK"

    # terminal wrong-ops -> auto-closed on the async path
    ALREADY_PUBLISHED = "ALREADY_PUBLISHED"
    OPEN_DUPLICATE = "OPEN_DUPLICATE"

    # fixable submissions -> PR stays open, user iterates
    CONTENT_DUPLICATE = "CONTENT_DUPLICATE"
    INVALID_CONTENT = "INVALID_CONTENT"
    MISSING_FILES = "MISSING_FILES"
    UNKNOWN_DEPENDENCY = "UNKNOWN_DEPENDENCY"
    NOT_FOUND = "NOT_FOUND"
    INVALID_STATE = "INVALID_STATE"

    # transient / infrastructure -> retried, never closed
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    PARSE_ERROR = "PARSE_ERROR"

    # codes whose PR should be auto-closed on the async (pipeline/server) path
    TERMINAL_DUPLICATES = frozenset({ALREADY_PUBLISHED, OPEN_DUPLICATE})

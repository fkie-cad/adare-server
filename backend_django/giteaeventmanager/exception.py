

class TaskFailure(Exception):
    """A submit/ingest failure carrying a machine-readable ``code``.

    ``code`` is one of ``giteaeventmanager.errorcodes.SubmitErrorCode`` (or
    ``None`` for an untagged internal invariant). It is surfaced in the 400
    response body so callers can act on the category, not the message string.
    """

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class GiteaAuthException(TaskFailure):
    pass


class NotUsedException(Exception):
    pass

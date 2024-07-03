

class TaskFailure(Exception):
    pass


class GiteaAuthException(TaskFailure):
    pass


class NotUsedException(Exception):
    pass

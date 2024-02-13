import re
from giteaeventmanager.action.factory import PullRequestHandlerFactory
from giteaeventmanager.exception import TaskFailure

import logging
log = logging.getLogger(__name__)


def pull_request_action(json_data) -> (bool, str):
    # determine type of the pull request (experiment create, experiment update, experiment delete, experiment assign, experiment unassign) by checking the title
    title = json_data["pull_request"]["title"]
    pull_request_action = json_data["action"]
    # parse title as it is in the format "[exp create] <experiment name>"
    pattern = r"\[(?P<objective>\w+) (?P<action>\w+)\] (?P<name>.+)"
    match = re.match(pattern, title)
    if not match:
        raise TaskFailure(f'could not parse title: {title}')

    objective = match.group("objective")
    action = match.group("action")
    object_name = match.group("name")
    # strip whitespaces from experiment name
    object_name = object_name.strip()

    # create a PullRequest object
    pull_request = PullRequestHandlerFactory.get_action(pull_request_action, json_data, objective, action, object_name)
    # execute the check
    pull_request.check()
    pull_request.action()

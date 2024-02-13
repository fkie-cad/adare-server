from giteaeventmanager.action.base import *
from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.action.plugin import TestfunctionsetPlugin, ExperimentPlugin


class PullRequestHandlerFactory:
    @staticmethod
    def get_action(pull_request_action: str, json_data: dict, objective: str, action: str, object_name: str) -> PullRequest:
        if objective == "testfunctionset":
            plugin = TestfunctionsetPlugin(
                objective=objective,
                object_name=object_name,
                last_commit=json_data["pull_request"]["head"]["sha"],
            )
        elif objective == "experiment":
            plugin = ExperimentPlugin(
                objective=objective,
                object_name=object_name,
                last_commit=json_data["pull_request"]["head"]["sha"],
            )
        else:
            raise TaskFailure(f'unknown objective "{objective}"')

        if pull_request_action == "label_updated":
            return PRLabelUpdated(
                plugin,
                json_data,
                objective,
                action,
                object_name,
            )
        elif pull_request_action == "assigned":
            return PRAssigned(
                plugin,
                json_data,
                objective,
                action,
                object_name,
            )
        elif pull_request_action == "unassigned":
            return PRUnassigned(
                plugin,
                json_data,
                objective,
                action,
                object_name,
            )
        elif pull_request_action == "review_requested":
            return PRReviewRequested(
                plugin,
                json_data,
                objective,
                action,
                object_name,
            )

        if action == "create":
            if pull_request_action == "opened":
                return PROpenedCreate(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif pull_request_action == "closed":
                return PRClosed(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif pull_request_action == "edited":
                return PREditedCreate(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            else:
                raise TaskFailure(f'unknown pull request action "{pull_request_action}"')
        elif action == "modify":
            if pull_request_action == "opened":
                return PROpenedModify(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif pull_request_action == "closed":
                return PRClosedModify(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif pull_request_action == "edited":
                return PREditedModify(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            else:
                raise TaskFailure(f'unknown pull request action "{pull_request_action}"')
        elif action == "delete":
            if pull_request_action == "opened":
                return PROpenedDelete(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif pull_request_action == "closed":
                return PRClosedDelete(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif pull_request_action == "edited":
                return PREditedDelete(
                    plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            else:
                raise TaskFailure(f'unknown pull request action "{pull_request_action}"')
        else:
            raise TaskFailure(f'unknown action "{action}"')


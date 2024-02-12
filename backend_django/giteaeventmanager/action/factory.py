from giteaeventmanager.action.base import PullRequest, PRClosedCreate, PROpenedCreate
from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.action.plugin import TestfunctionsetPlugin


class PullRequestHandlerFactory:
    @staticmethod
    def get_action(pull_request_action: str, json_data: dict, objective: str, action: str, object_name: str) -> PullRequest:
        if objective == "testfunctionset":
            testfunctionset_plugin = TestfunctionsetPlugin(
                objective=objective,
                object_name=object_name,
                last_commit=json_data["pull_request"]["head"]["sha"],
            )
            if action == "create" and pull_request_action == "opened":
                return PROpenedCreate(
                    testfunctionset_plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            elif action == "create" and pull_request_action == "closed":
                return PRClosedCreate(
                    testfunctionset_plugin,
                    json_data,
                    objective,
                    action,
                    object_name,
                )
            else:
                raise TaskFailure(f'unknown action "{action}"')
        else:
            raise TaskFailure(f'unknown objective "{objective}"')



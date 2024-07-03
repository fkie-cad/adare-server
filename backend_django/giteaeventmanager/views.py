import rest_framework.parsers
from rest_framework import views, generics
from rest_framework.response import Response
import rest_framework.status as http_status_codes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from celery import shared_task
from giteaeventmanager.event import pull_request_action
from experiments.models import RequestCreationMessage, Request
from giteaeventmanager.exception import TaskFailure, NotUsedException

import logging
log = logging.getLogger(__name__)
# set log level to also show debug messages
log.setLevel(logging.DEBUG)


@shared_task
def handle_gitea_webhook(json_data):
    try:
        if json_data["repository"]["name"] != settings.GITEA_EXPERIMENTS_REPO:
            log.error(f'got webhook from repo {json_data["repository"]} but expected {settings.GITEA_EXPERIMENTS_REPO}')
            raise TaskFailure(f'got webhook from repo {json_data["repository"]} but expected {settings.GITEA_EXPERIMENTS_REPO}')

        if json_data["repository"]["owner"]["login"] != settings.GITEA_EXPERIMENTS_REPO_OWNER:
            log.error(f'repo owner is not the expected {settings.GITEA_EXPERIMENTS_REPO_OWNER}')
            raise TaskFailure('repo owner is not the expected {settings.GITEA_EXPERIMENTS_REPO_OWNER}')

        pull_request_action(json_data)

    except TaskFailure as e:
        error_msg = str(e)
        gitea_pr_id = json_data["number"]
        RequestCreationMessage.objects.get_or_create(
            gitea_pr_number=gitea_pr_id,
            error_message=error_msg
        )
        # todo: maybe don't raise the exception here to let the task seem successful
        raise e
    except NotUsedException as e:
        return str(e)


class GiteaWebhookView(views.APIView):
    parser_classes = [rest_framework.parsers.JSONParser]
    permission_classes = [AllowAny]

    def post(self, request):
        json_data = request.data
        if not json_data:
            return Response(status=http_status_codes.HTTP_400_BAD_REQUEST)

        # handle webhook
        if 'pull_request' in json_data.keys():
            handle_gitea_webhook.delay(json_data)

        # return a response
        return Response(status=http_status_codes.HTTP_200_OK)


class RequestCheckView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # get secret from request
        secret = request.query_params.get("secret")
        if not secret:
            return Response(status=http_status_codes.HTTP_400_BAD_REQUEST)

        # check if secret is correct
        if secret != settings.GITEA_WEBHOOK_SECRET:
            return Response(status=http_status_codes.HTTP_401_UNAUTHORIZED)

        # get gitea pr id
        gitea_pr_id = request.query_params.get("prnumber")
        if not gitea_pr_id:
            return Response(status=http_status_codes.HTTP_400_BAD_REQUEST)

        # get request
        try:
            request = Request.objects.get(gitea_pr_number=gitea_pr_id)
        except Request.DoesNotExist:
            # get error message
            try:
                error_msg = RequestCreationMessage.objects.get(gitea_pr_number=gitea_pr_id).error_message
            except RequestCreationMessage.DoesNotExist:
                error_msg = "unknown error"
            return Response(data={"error": error_msg}, status=http_status_codes.HTTP_404_NOT_FOUND)

        # return response
        return Response(status=http_status_codes.HTTP_200_OK)



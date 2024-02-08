import rest_framework.parsers
from rest_framework import views
from rest_framework.response import Response
import rest_framework.status as http_status_codes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from celery import shared_task
from giteaeventmanager.event import pull_request_opened
from adare.celery import celery_log

import logging
log = logging.getLogger(__name__)


class TaskFailure(Exception):
    pass



@shared_task
def handle_gitea_webhook(request, json_data):
    if json_data["repository"]["name"] != settings.GITEA_REPO_NAME:
        celery_log.error(f'got webhook from repo {json_data["repository"]} but expected {settings.GITEA_REPO_NAME}')
        return

    if json_data["repository"]["owner"]["login"] != settings.GITEA_EXPERIMENTS_REPO_OWNER:
        celery_log.error(f'repo owner is not the expected {settings.GITEA_EXPERIMENTS_REPO_OWNER}')
        return

    if json_data["secret"] != settings.GITEA_WEBHOOK_SECRET:
        celery_log.error(f'got webhook with wrong secret')
        return

    # check if pull request was opened
    if json_data["action"] == "opened":
        success, msg = pull_request_opened(request, json_data)
        if not success:
            raise TaskFailure(msg)



class GiteaWebhookView(views.APIView):
    parser_classes = [rest_framework.parsers.JSONParser]
    permission_classes = [AllowAny]

    def post(self, request):
        json_data = request.data
        if not json_data:
            return Response("no json data", status=http_status_codes.HTTP_400_BAD_REQUEST)

        # handle webhook
        handle_gitea_webhook.delay(request, json_data)

        # return a response
        return Response(status=http_status_codes.HTTP_200_OK)

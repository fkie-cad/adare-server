import rest_framework.parsers
from rest_framework import views
from rest_framework.response import Response
import rest_framework.status as http_status_codes
from rest_framework.permissions import AllowAny, IsAuthenticated

import logging

log = logging.getLogger(__name__)


def handle_gitea_webhook(json_data):
    log.warning("got webhook")
    log.warning(json_data)


class GiteaWebhookView(views.APIView):
    parser_classes = [rest_framework.parsers.JSONParser]
    permission_classes = [AllowAny]

    def post(self, request):
        json_data = request.data
        if not json_data:
            return Response("no json data", status=http_status_codes.HTTP_400_BAD_REQUEST)

        log.warning(request.headers)
        # handle webhook
        handle_gitea_webhook(json_data)

        # return a response
        return Response(status=http_status_codes.HTTP_200_OK)


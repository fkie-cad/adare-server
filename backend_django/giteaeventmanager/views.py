from rest_framework import views
from rest_framework.response import Response
import rest_framework.status as http_status_codes
from rest_framework.permissions import AllowAny
from django.conf import settings

from giteaeventmanager.exception import TaskFailure
from giteaeventmanager.service import ingest_pr, finalize_pr

import logging
log = logging.getLogger(__name__)


def _authorize_secret(request):
    """Shared ?secret= auth for the internal ingest/finalize endpoints.

    Returns an error Response when unauthorized, otherwise None.
    """
    secret = request.query_params.get("secret")
    if not secret:
        return Response(status=http_status_codes.HTTP_400_BAD_REQUEST)
    if secret != settings.GITEA_WEBHOOK_SECRET:
        log.warning(f'rejected {request.path} call with an invalid secret')
        return Response(status=http_status_codes.HTTP_401_UNAUTHORIZED)
    return None


def _get_prnumber(request):
    """Parse and validate the ?prnumber= query parameter. Returns (prnumber, error_response)."""
    raw = request.query_params.get("prnumber")
    if not raw:
        return None, Response(status=http_status_codes.HTTP_400_BAD_REQUEST)
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return None, Response(data={"error": "prnumber must be an integer"},
                              status=http_status_codes.HTTP_400_BAD_REQUEST)


class GiteaIngestView(views.APIView):
    """Synchronously ingest a PR into a draft object (idempotent upsert)."""
    permission_classes = [AllowAny]

    def post(self, request):
        if (unauthorized := _authorize_secret(request)) is not None:
            return unauthorized
        prnumber, error = _get_prnumber(request)
        if error is not None:
            return error
        try:
            result = ingest_pr(prnumber)
        except TaskFailure as e:
            log.warning(f'ingest failed for pr {prnumber}: {e}')
            return Response(data={"error": str(e), "code": e.code},
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        return Response(data=result, status=http_status_codes.HTTP_200_OK)


class GiteaFinalizeView(views.APIView):
    """Finalize a closed PR: publish on merge, remove the draft on non-merge close."""
    permission_classes = [AllowAny]

    def post(self, request):
        if (unauthorized := _authorize_secret(request)) is not None:
            return unauthorized
        prnumber, error = _get_prnumber(request)
        if error is not None:
            return error
        try:
            result = finalize_pr(prnumber)
        except TaskFailure as e:
            log.warning(f'finalize failed for pr {prnumber}: {e}')
            return Response(data={"error": str(e), "code": e.code},
                            status=http_status_codes.HTTP_400_BAD_REQUEST)
        return Response(data=result, status=http_status_codes.HTTP_200_OK)

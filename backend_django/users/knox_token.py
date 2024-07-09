from django.http import HttpRequest
from knox.views import LoginView


import logging
log = logging.getLogger(__name__)


class TokenStrategy:
    @classmethod
    def obtain(cls, user):
        request = HttpRequest()
        request.method = "POST"
        request.user = user
        request._force_auth_user = user
        val = LoginView.as_view()(request)
        # needed since https://github.com/sunscrapers/djoser/blob/master/djoser/social/serializers.py normally expect an JWT token
        return {
            'access': val.data['token'],
        }

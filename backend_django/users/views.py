from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.gitea.views import GiteaOAuth2Adapter
from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.registration.views import SocialLoginView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import urllib
from rest_framework import generics
from rest_framework import permissions
from users.models import Profile
from django.conf import settings
import urllib.parse
from users.serializers import ProfileSerializer, PublicProfileSerializer
from users import tasks
from rest_framework import views, status
from rest_framework.response import Response
from knox.models import AuthToken

import logging

log = logging.getLogger(__name__)


class GiteaLoginView(SocialLoginView):
    adapter_class = GiteaOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.FRONTEND_URL + '/login/oauth/'


    def get_response(self):
        # get extra data sent by gitea
        user_extra_data = SocialAccount.objects.filter(user=self.request.user).first().extra_data

        profile = self.user.profile
        profile.avatar = user_extra_data.get('avatar_url')
        profile.save()

        #response_data = self.token
        token_instance, token = AuthToken.objects.create(self.request.user)

        response_data = {
            'user': self.user.username,
            'token': token,
            'expiry': token_instance.expiry,
        }

        # update gitea user
        tasks.update_gitea_user.delay(
            django_user_id=self.user.id,
            gitea_user_id=user_extra_data.get('id'),
            username=self.user.username,
            email=self.user.email,
            avatar=user_extra_data.get('avatar_url'),
        )

        # update teams but do not block the response
        tasks.update_teams.delay(self.request.user.username, )

        return Response(response_data, status=status.HTTP_200_OK)


class GiteaRedirectView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        # get state from url
        state = request.GET.get('state', None)
        # get redirect uri from url
        redirect_uri = request.GET.get('redirect_uri', None)

        if not state:
            return Response({'error': 'no state provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not redirect_uri:
            return Response({'error': 'no redirect_uri provided'}, status=status.HTTP_400_BAD_REQUEST)

        # return the gitea url for login
        client_id = settings.SOCIALACCOUNT_PROVIDERS['gitea']['APP']['client_id']
        gitea_url = settings.GITEA_URL_OUTSIDE
        # encode redirect uri to be url safe
        redirect_uri = urllib.parse.quote(redirect_uri, safe='')
        gitea_oauth_url = f'{gitea_url}login/oauth/authorize?client_id={client_id}&response_type=code&state={state}&redirect_uri={redirect_uri}'
        return Response({'url': gitea_oauth_url}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile

    @method_decorator(csrf_protect, 'dispatch')
    def update(self, request, *args, **kwargs):
        raise NotImplementedError


class PublicProfileView(generics.RetrieveAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PublicProfileSerializer

    def get_object(self):
        try:
            return Profile.objects.get(user__username=self.kwargs['username'])
        except Profile.DoesNotExist:
            return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)


class CSRFView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    @method_decorator(ensure_csrf_cookie, 'dispatch')
    def get(self, request):
        return Response(status=status.HTTP_200_OK)


class DevLoginView(views.APIView):
    """Dev-only login that creates a local user + Knox token without Gitea."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        from decouple import config
        if config('MODE', default='production') != 'development':
            return Response({'error': 'not available'}, status=status.HTTP_403_FORBIDDEN)

        from django.contrib.auth.models import User
        from users.models import GiteaUser

        username = request.data.get('username', 'devuser')

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@localhost'},
        )

        GiteaUser.objects.get_or_create(
            user=user,
            defaults={
                'gitea_id': 99999,
                'username': username,
                'email': user.email,
            },
        )

        token_instance, token = AuthToken.objects.create(user)

        return Response({
            'user': user.username,
            'token': token,
            'expiry': token_instance.expiry,
        }, status=status.HTTP_200_OK)

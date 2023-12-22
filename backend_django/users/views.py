from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, get_token
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from PIL import Image
from sorl.thumbnail import get_thumbnail, delete

from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework import views
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.serializers import LoginSerializer, PrivateProfileSerializer, ProfileAvatarSerializer, ProfileSerializer, PublicProfileSerializer
from users.models import Profile

# knox imports
from knox.views import LoginView as KnoxLoginView


import logging
logger = logging.getLogger(__name__)


class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    @method_decorator(csrf_protect, 'dispatch')
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super().post(request, format=None)


class ProfileViewLoggedIn(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PrivateProfileSerializer

    def get_object(self):
        return self.request.user.profile

    @method_decorator(csrf_protect, 'dispatch')
    def update(self, request, *args, **kwargs):
        raise NotImplementedError


class ProfileAvatarViewLoggedIn(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileAvatarSerializer

    def get_object(self):
        return self.request.user.profile

    @method_decorator(csrf_protect, 'dispatch')
    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile.avatar:
            delete(profile.avatar, delete_file=False)
            profile.avatar.delete()
        profile.avatar = request.FILES.get('avatar')
        profile.save()
        messages.success(request, 'avatar was successfully updated!')
        return Response(status=status.HTTP_200_OK)

    @method_decorator(csrf_protect, 'dispatch')
    def delete(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile.avatar:
            delete(profile.avatar, delete_file=False)
            profile.avatar.delete()
        messages.success(request, 'avatar was successfully deleted!')
        return Response(status=status.HTTP_200_OK)


class ProfileAvatarView(generics.RetrieveAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProfileAvatarSerializer

    def get_object(self):
        # get url parameter
        username = self.kwargs.get('username', None)
        # get profile
        try:
            profile = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            profile = None
        return profile


class ProfileView(generics.RetrieveAPIView):
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        if not self.request.user.is_authenticated:
            return PublicProfileSerializer
        else:
            return ProfileSerializer

    def get_object(self):
        # get url parameter
        username = self.kwargs.get('username', None)

        # get profile
        try:
            profile = Profile.objects.get(user__username=username)
        except Profile.DoesNotExist:
            profile = None

        return profile


class SupervisorListViewNames(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        profiles = Profile.objects.filter(user__groups__name__contains='supervisor')
        return Response([p.user.username for p in profiles.all()], status=status.HTTP_200_OK)


class CSRFView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    @method_decorator(ensure_csrf_cookie, 'dispatch')
    def get(self, request):
        return Response(status=status.HTTP_200_OK)


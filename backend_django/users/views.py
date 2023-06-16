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

from users.serializers import LoginSerializer, ProfileSerializer, ProfileAvatarSerializer
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


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile

    @method_decorator(csrf_protect, 'dispatch')
    def update(self, request, *args, **kwargs):
        raise NotImplementedError


class ProfileAvatarView(generics.RetrieveUpdateDestroyAPIView):
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


class CSRFView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    @method_decorator(ensure_csrf_cookie, 'dispatch')
    def get(self, request):
        return Response(status=status.HTTP_200_OK)

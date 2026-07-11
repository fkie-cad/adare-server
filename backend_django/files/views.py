import rest_framework.generics as generics
from django.shortcuts import redirect
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from decouple import config
from users.models import User
from experiments.models import ExperimentRun, Experiment
from pathlib import Path

MODE = config('MODE', default='production')


def get_response(filepath: str, disposition: str = 'inline', typ: str = 'media'):
    response = Response()
    response.headers['Content-Disposition'] = disposition
    if MODE == 'production':
        response['X-Accel-Redirect'] = f'/protected/{typ}/{filepath}'
    else:
        # no nginx so redirect to the media file directly
        response = redirect(f'http://localhost:8000/{typ}/{filepath}')
    return response

#
# class AvatarThumbnailFileView(generics.RetrieveAPIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request, *args, **kwargs):
#         # get username from url
#         username = kwargs['username']
#         # get thumbnail size from url
#         size = kwargs['size']
#         # get user
#         user = User.objects.get(username=username)
#         if not user.profile.avatar:
#             return Response(status=404)
#
#         # get filepath of thumbnail
#         if size == 'sm':
#             filepath = serializer.data['avatar_thumbnail_sm']
#         elif size == 'md':
#             filepath = serializer.data['avatar_thumbnail_md']
#         elif size == 'lg':
#             filepath = serializer.data['avatar_thumbnail_lg']
#         elif size == 'orig':
#             filepath = serializer.data['avatar']
#         else:
#             return Response(status=404)
#         # strip leading /media/ from filepath
#         filepath = filepath[7:]
#
#         return get_response(filepath)


class LogFileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # get experiment run id from url
        experiment_run_uuid = kwargs['experimentrun_uuid']
        # get experiment run
        experiment_run = ExperimentRun.objects.get(uuid=experiment_run_uuid)
        if not experiment_run.logfile:
            return Response(status=400)
        # get filepath of logfile
        filepath = experiment_run.logfile.name
        disposition = f'attachment; filename="{experiment_run_uuid}.log"'
        return get_response(filepath, disposition=disposition)


class PlaybookFileView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # get experiment id from url
        experiment_uuid = kwargs['experiment_uuid']
        # get experiment
        experiment = Experiment.objects.get(uuid=experiment_uuid)
        if not experiment.playbook_file:
            return Response(status=404)
        # get filepath of playbookfile
        filepath = experiment.playbook_file.name
        return get_response(filepath)


class AchievementIconView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # get achievement name from url
        achievement_name = kwargs['achievement_name']
        filepath = f'achievements/{achievement_name}'
        return get_response(filepath, typ='static')

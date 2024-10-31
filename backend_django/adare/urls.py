"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import urllib

from django.contrib import admin
from django.shortcuts import redirect

import users.views as users_views
import experiments.views as experiment_frontend_views
import files.views as files_views
import giteaeventmanager.views as giteaeventmanager_views
from knox.views import LogoutView as KnoxLogoutView
from django.conf.urls.static import static
from django.urls import path, include, re_path
from decouple import config
from django.conf import settings
from allauth.socialaccount.providers.gitea import views as gitea_views

MODE = config('MODE', default='production')


urlpatterns = [
    # admin page
    path('admin/', admin.site.urls),

    # CSRF token retrieval for frontend
    path('api/csrf/', users_views.CSRFView.as_view()),

    # ### authentication urls ###
    path('api/auth/gitea/', users_views.GiteaLoginView.as_view(), name='socialaccount_signup'),
    path('api/auth/gitea/callback/', users_views.GiteaRedirectView.as_view()),

    # ### user profile urls ###
    # get the profile of the logged-in user
    path('api/user/profile/', users_views.ProfileView.as_view()),
    # get the profile of a user by username
    path('api/user/<str:username>/profile/', users_views.PublicProfileView.as_view()),

    # ### scenario urls ###
    # get all scenarios (paginated, filtered, sorted)
    # path('api/scenario/', experiment_frontend_views.ScenarioListView.as_view()),
    # path('api/scenario/filteroptions/', experiment_frontend_views.ScenarioFilterOptionsView.as_view()),

    # ### experiment urls ###
    # get all experiments (paginated, filtered, sorted)
    path('api/experiment/', experiment_frontend_views.ExperimentListView.as_view()),
    # # get a single experiment by uuid
    path('api/experiment/experiment_<str:ulid>/', experiment_frontend_views.ExperimentView.as_view()),
    # #
    path('api/download/experiment_<str:ulid>/', experiment_frontend_views.ExperimentDownloadView.as_view()),

    # #
    path('api/experiment/filteroptions/', experiment_frontend_views.ExperimentFilterOptionsView.as_view()),
    # # check if an experiment is published to the webapp if yes, return the experiment information
    path('api/experiment/check/', experiment_frontend_views.ExperimentCheckView.as_view()),
    path('api/experiment/checkmuliple/', experiment_frontend_views.ExperimentCheckMultipleView.as_view()),
    #
    # # ### run urls ###
    # # get all experiment runs (paginated, filtered, sorted)
    path('api/run/', experiment_frontend_views.ExperimentRunListView.as_view()),
    # # get a single experiment run by uuid
    path('api/run/run_<str:uuid>/', experiment_frontend_views.ExperimentRunRetrieveView.as_view()),
    # #
    # path('api/experimentrun/publish/', experiment_frontend_views.ExperimentRunPublishView.as_view()),
    # # check if an experiment run is published to the webapp
    path('api/run/check/', experiment_frontend_views.ExperimentRunCheckView.as_view()),
    path('api/run/delete/run_<str:ulid>/', experiment_frontend_views.ExperimentRunDeleteView.as_view()),
    path('api/run/publish/', experiment_frontend_views.ExperimentRunPublishView.as_view()),


    path('api/environment/', experiment_frontend_views.EnvironmentListView.as_view()),
    path('api/environment/filteroptions/', experiment_frontend_views.EnvironmentFilterOptionsView.as_view()),
    path('api/download/environment_<str:name>/', experiment_frontend_views.EnvironmentDownloadView.as_view()),

    path('api/download/testfunction_<str:name>/', experiment_frontend_views.TestfunctionDownloadView.as_view()),

    path('api/hash/experiment_<str:sha256hash>/', experiment_frontend_views.ExperimentHashToMetadataView.as_view()),
    path('api/hash/environment_<str:sha256hash>/', experiment_frontend_views.EnvironmentHashToMetadataView.as_view()),
    path('api/hash/testfunction_<str:sha256hash>/', experiment_frontend_views.TestfunctionHashToMetadataView.as_view()),

    # ### testfunction urls ###
    path('api/testfunction/', experiment_frontend_views.TestFunctionListView.as_view()),

    # ### request urls ###
    # get all requests (paginated, filtered, sorted)
    path('api/request/', experiment_frontend_views.RequestListView.as_view()),
    # # get a single request by uuid
    path('api/request/request_<str:uuid>/', experiment_frontend_views.RequestRetrieveView.as_view()),
    # #
    path('api/request/filteroptions/', experiment_frontend_views.RequestFilterOptionsView.as_view()),

    # ### protected file access urls ###
    # path('api/file/avatar/<str:username>/thumbnail/<str:size>/', files_views.AvatarThumbnailFileView.as_view()),
    # path('api/file/logfile/<str:experimentrun_uuid>/', files_views.LogFileView.as_view()),
    # path('api/file/actionfile/<str:experiment_uuid>/', files_views.ActionFileView.as_view()),
    # path('api/file/testsetfile/<str:experiment_uuid>/', files_views.TestsetFileView.as_view()),
    # path('api/file/achievements/<str:achievement_name>/', files_views.AchievementIconView.as_view()),

    # ### statistics urls ###
    path('api/stats/', experiment_frontend_views.StatisticView.as_view()),

    # ### gitea webhook url ###
    # !!!! NEVER EXPOSE THIS URL TO THE PUBLIC INTERNET !!!!
    path('internal/gitea/webhook/', giteaeventmanager_views.GiteaWebhookView.as_view()),
    path('internal/gitea/requestcheck/', giteaeventmanager_views.RequestCheckView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
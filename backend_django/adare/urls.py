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
from django.contrib import admin

import users.views as users_views
import experiments.views as experiment_frontend_views
import files.views as files_views
import giteaeventmanager.views as giteaeventmanager_views
from knox.views import LogoutView as KnoxLogoutView
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.conf import settings
from decouple import config

MODE = config('MODE', default='production')


urlpatterns = [
    # admin page
    path('admin/', admin.site.urls),

    # CSRF token retrieval for frontend
    path('api/csrf/', users_views.CSRFView.as_view()),

    # ### authentication urls ###
    path(r'auth/', include('djoser.social.urls')),


    # ### user profile urls ###
    # get the profile of the logged-in user
    path('api/user/profile/', users_views.ProfileViewLoggedIn.as_view()),
    # get a list of all supervisors (only usernames)
    path('api/user/supervisors/names/', users_views.SupervisorListViewNames.as_view()),
    # get the avatar of the logged-in user
    path('api/user/profile/avatar/', users_views.ProfileAvatarViewLoggedIn.as_view()),
    # get the profile of a user by username
    path('api/user/<str:username>/profile/', users_views.ProfileView.as_view()),
    # get the avatar of a user by username
    path('api/user/<str:username>/profile/avatar/', users_views.ProfileAvatarView.as_view()),

    # ### scenario urls ###
    # get all scenarios (paginated, filtered, sorted)
    path('api/scenario/', experiment_frontend_views.ScenarioListView.as_view()),
    #
    path('api/scenario/filteroptions/', experiment_frontend_views.ScenarioFilterOptionsView.as_view()),
    # create a new scenario (only for supervisors) - ONLY FOR TESTING SINCE SCENARIOS ARE CREATED VIA REQUESTS
    path('api/scenario/create/', experiment_frontend_views.ScenarioCreateView.as_view()),

    # ### experiment urls ###
    # get all experiments (paginated, filtered, sorted)
    path('api/experiment/', experiment_frontend_views.ExperimentListView.as_view()),
    # get a single experiment by uuid
    path('api/experiment/experiment_<str:uuid>/', experiment_frontend_views.ExperimentRetrieveView.as_view()),
    # get all experiments for a given scenario (by scenario uuid)
    path('api/experiment/scenario_<str:uuid>/', experiment_frontend_views.ExperimentByScenarioListView.as_view()),
    #
    path('api/experiment/filteroptions/', experiment_frontend_views.ExperimentFilterOptionsView.as_view()),
    # create a new experiment (only for supervisors) - ONLY FOR TESTING SINCE EXPERIMENTS ARE CREATED VIA REQUESTS
    path('api/experiment/create/', experiment_frontend_views.ExperimentCreateView.as_view()),
    # check if an experiment is published to the webapp if yes, return the experiment information
    path('api/experiment/check/', experiment_frontend_views.ExperimentCheckView.as_view()),
    path('api/experiment/checkmuliple/', experiment_frontend_views.ExperimentCheckMultipleView.as_view()),

    # ### experiment run urls ###
    # get all experiment runs (paginated, filtered, sorted)
    path('api/experimentrun/', experiment_frontend_views.ExperimentRunListView.as_view()),
    # get a single experiment run by uuid
    path('api/experimentrun/experimentrun_<str:uuid>/', experiment_frontend_views.ExperimentRunRetrieveView.as_view()),
    #
    path('api/experimentrun/publish/', experiment_frontend_views.ExperimentRunPublishView.as_view()),
    # check if an experiment run is published to the webapp
    path('api/experimentrun/check/', experiment_frontend_views.ExperimentRunCheckView.as_view()),



    # ### request urls ###
    # get all requests (paginated, filtered, sorted)
    path('api/request/', experiment_frontend_views.RequestListView.as_view()),
    # get a single request by uuid
    path('api/request/request_<str:uuid>/', experiment_frontend_views.RequestRetrieveView.as_view()),
    #
    path('api/request/filteroptions/', experiment_frontend_views.RequestFilterOptionsView.as_view()),
    # create a new request for an experiment
    path('api/request/experiment/create/', experiment_frontend_views.RequestsExperimentCreateView.as_view()),
    # create a new request for a scenario
    path('api/request/scenario/create/', experiment_frontend_views.RequestsScenarioCreateView.as_view()),
    # request to assign an experiment to a scenario
    path('api/request/assign/create/', experiment_frontend_views.RequestAssignCreateView.as_view()),
    # accept a request (only for supervisors)
    path('api/request/<str:uuid>/accept/', experiment_frontend_views.RequestAcceptView.as_view()),
    # reject a request (only for supervisors)
    path('api/request/<str:uuid>/reject/', experiment_frontend_views.RequestRejectView.as_view()),
    # cancel a request (only for requestor)
    path('api/request/<str:uuid>/cancel/', experiment_frontend_views.RequestCancelView.as_view()),
    # assign a request to a supervisor (only for supervisors)
    path('api/request/<str:uuid>/assign/<str:username>/', experiment_frontend_views.RequestAssignView.as_view()),
    # check request status
    path('api/request/check/', experiment_frontend_views.RequestCheckView.as_view()),

    # ### protected file access urls ###
    path('api/file/avatar/<str:username>/thumbnail/<str:size>/', files_views.AvatarThumbnailFileView.as_view()),
    path('api/file/logfile/<str:experimentrun_uuid>/', files_views.LogFileView.as_view()),
    path('api/file/actionfile/<str:experiment_uuid>/', files_views.ActionFileView.as_view()),
    path('api/file/testsetfile/<str:experiment_uuid>/', files_views.TestsetFileView.as_view()),
    path('api/file/achievements/<str:achievement_name>/', files_views.AchievementIconView.as_view()),

    # ### statistics urls ###
    path('api/statistics/', experiment_frontend_views.StatisticView.as_view()),

    # ### gitea webhook url ###
    path('internal/gitea/webhook/', giteaeventmanager_views.GiteaWebhookView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
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
from django.conf.urls.static import static
from django.urls import path, include, re_path
from decouple import config
from django.conf import settings

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

    # ### experiment urls ###
    # get all experiments (paginated, filtered, sorted)
    path('api/experiment/', experiment_frontend_views.ExperimentListView.as_view()),
    # # get a single experiment by uuid
    path('api/experiment/experiment_<str:ulid>/', experiment_frontend_views.ExperimentView.as_view()),
    # #
    path('api/download/experiment_<str:ulid>/', experiment_frontend_views.ExperimentDownloadView.as_view()),

    # #
    path('api/experiment/filteroptions/', experiment_frontend_views.ExperimentFilterOptionsView.as_view()),
    path('api/experiment/dashboard/', experiment_frontend_views.ExperimentDashboardView.as_view()),
    # # check if an experiment is published to the webapp if yes, return the experiment information
    path('api/experiment/check/', experiment_frontend_views.ExperimentCheckView.as_view()),
    path('api/experiment/checkmuliple/', experiment_frontend_views.ExperimentCheckMultipleView.as_view()),
    #
    # # ### run urls ###
    # # get all experiment runs (paginated, filtered, sorted)
    path('api/run/', experiment_frontend_views.ExperimentRunListView.as_view()),
    # # get a single experiment run by uuid
    path('api/run/run_<str:ulid>/', experiment_frontend_views.ExperimentRunRetrieveView.as_view()),
    # #
    # check if an experiment run is published to the webapp
    path('api/run/check/', experiment_frontend_views.ExperimentRunCheckView.as_view()),
    path('api/run/delete/run_<str:ulid>/', experiment_frontend_views.ExperimentRunDeleteView.as_view()),
    path('api/run/publish/', experiment_frontend_views.ExperimentRunPublishView.as_view()),


    path('api/environment/', experiment_frontend_views.EnvironmentListView.as_view()),
    path('api/environment/filteroptions/', experiment_frontend_views.EnvironmentFilterOptionsView.as_view()),
    path('api/environment/environment_<str:name>/', experiment_frontend_views.EnvironmentView.as_view()),
    path('api/download/environment_<str:name>/', experiment_frontend_views.EnvironmentDownloadView.as_view()),

    path('api/download/testfunction_<str:name>/', experiment_frontend_views.TestfunctionDownloadView.as_view()),

    path('api/hash/experiment_<str:sha256hash>/', experiment_frontend_views.ExperimentHashToMetadataView.as_view()),
    path('api/hash/environment_<str:sha256hash>/', experiment_frontend_views.EnvironmentHashToMetadataView.as_view()),
    path('api/hash/testfunction_<str:sha256hash>/', experiment_frontend_views.TestfunctionHashToMetadataView.as_view()),

    # ### testfunction urls ###
    path('api/testfunction/', experiment_frontend_views.TestFunctionListView.as_view()),
    path('api/testfunction/filteroptions/', experiment_frontend_views.TestfunctionFilterOptionsView.as_view()),

    # ### request urls ###
    # get all requests (paginated, filtered, sorted)
    path('api/request/', experiment_frontend_views.RequestListView.as_view()),
    # # get a single request by uuid
    path('api/request/request_<str:ulid>/', experiment_frontend_views.RequestRetrieveView.as_view()),
    # #
    path('api/request/filteroptions/', experiment_frontend_views.RequestFilterOptionsView.as_view()),

    # ### statistics urls ###
    path('api/stats/', experiment_frontend_views.StatisticView.as_view()),

    # ### achievement icon urls ###
    path('api/file/achievements/<str:achievement_name>/', files_views.AchievementIconView.as_view()),

    # ### gitea webhook url ###
    # !!!! NEVER EXPOSE THIS URL TO THE PUBLIC INTERNET !!!!
    path('internal/gitea/webhook/', giteaeventmanager_views.GiteaWebhookView.as_view()),
    path('internal/gitea/requestcheck/', giteaeventmanager_views.RequestCheckView.as_view()),

]

if MODE == 'development':
    import experiments.dev_views as dev_views
    urlpatterns += [
        path('api/auth/dev/', users_views.DevLoginView.as_view()),
        path('api/submit/experiment/', dev_views.DevSubmitExperimentView.as_view()),
        path('api/submit/testfunction/', dev_views.DevSubmitTestfunctionView.as_view()),
        path('api/submit/environment/', dev_views.DevSubmitEnvironmentView.as_view()),
    ]
else:
    import experiments.submit_views as submit_views
    urlpatterns += [
        path('api/submit/experiment/', submit_views.SubmitExperimentView.as_view()),
        path('api/submit/testfunction/', submit_views.SubmitTestfunctionView.as_view()),
        path('api/submit/environment/', submit_views.SubmitEnvironmentView.as_view()),
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
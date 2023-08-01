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
from django.urls import path

import users.views as users_views
import experiments.views as experiment_frontend_views
from knox.views import LogoutView as KnoxLogoutView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # admin page
    path('admin/', admin.site.urls),

    # CSRF token retrieval for frontend
    path('api/csrf/', users_views.CSRFView.as_view()),

    # ### authentication urls ###
    # login
    path('api/user/login/', users_views.LoginView.as_view()),
    # logout
    path('api/user/logout/', KnoxLogoutView.as_view()),

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
    # get a list of all unique entries for a given field (for filtering in frontend)
    path('api/scenario/filteroptions/<str:field>/', experiment_frontend_views.ScenarioFilterOptionsView.as_view()),
    # create a new scenario (only for supervisors) - ONLY FOR TESTING SINCE SCENARIOS ARE CREATED VIA REQUESTS
    path('api/scenario/create/', experiment_frontend_views.ScenarioCreateView.as_view()),

    # ### experiment urls ###
    # get all experiments (paginated, filtered, sorted)
    path('api/experiment/', experiment_frontend_views.ExperimentListView.as_view()),
    # get a single experiment by uuid
    path('api/experiment/experiment_<str:uuid>/', experiment_frontend_views.ExperimentRetrieveView.as_view()),
    # get all experiments for a given scenario (by scenario uuid)
    path('api/experiment/scenario_<str:uuid>/', experiment_frontend_views.ExperimentByScenarioListView.as_view()),
    # get a list of all unique entries for a given field (for filtering in frontend)
    path('api/experiment/filteroptions/<str:field>/', experiment_frontend_views.ExperimentFilterOptionsView.as_view()),
    # add an experiment run to an experiment
    path('api/experimentrun/create/', experiment_frontend_views.ExperimentRunCreateView.as_view()),
    # create a new experiment (only for supervisors) - ONLY FOR TESTING SINCE EXPERIMENTS ARE CREATED VIA REQUESTS
    path('api/experiment/create/', experiment_frontend_views.ExperimentCreateView.as_view()),


    # ### request urls ###
    # get all requests (paginated, filtered, sorted)
    path('api/request/', experiment_frontend_views.RequestListView.as_view()),
    # get a single request by uuid
    path('api/request/<str:uuid>/', experiment_frontend_views.RequestRetrieveView.as_view()),
    # get a list of all unique entries for a given field (for filtering in frontend)
    path('api/request/filteroptions/<str:field>/', experiment_frontend_views.RequestFilterOptionsView.as_view()),
    # create a new request for an experiment
    path('api/request/experiment/create/', experiment_frontend_views.RequestsExperimentCreateView.as_view()),
    # create a new request for a scenario
    path('api/request/scenario/create/', experiment_frontend_views.RequestsScenarioCreateView.as_view()),
    # accept a request (only for supervisors)
    path('api/request/<str:uuid>/accept/', experiment_frontend_views.RequestAcceptView.as_view()),
    # reject a request (only for supervisors)
    path('api/request/<str:uuid>/reject/', experiment_frontend_views.RequestRejectView.as_view()),
    # cancel a request (only for requestor)
    path('api/request/<str:uuid>/cancel/', experiment_frontend_views.RequestCancelView.as_view()),
    # assign a request to a supervisor (only for supervisors)
    path('api/request/<str:uuid>/assign/<str:username>/', experiment_frontend_views.RequestAssignView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

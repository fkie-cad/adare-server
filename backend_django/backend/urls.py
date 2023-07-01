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
import experiments.views.api_views as experiments_views
import experiments.views.frontend_views as experiment_frontend_views
from knox.views import LogoutView as KnoxLogoutView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/login/', users_views.LoginView.as_view()),
    path('api/user/logout/', KnoxLogoutView.as_view()),
    path('api/user/profile/', users_views.ProfileViewLoggedIn.as_view()),
    path('api/user/profile/avatar/', users_views.ProfileAvatarViewLoggedIn.as_view()),
    path('api/user/<str:username>/profile/', users_views.ProfileView.as_view()),
    path('api/user/<str:username>/profile/avatar/', users_views.ProfileAvatarView.as_view()),
    path('api/csrf/', users_views.CSRFView.as_view()),
    path('api/scenario/', experiment_frontend_views.ScenarioListView.as_view()),
    path('api/scenario/create/', experiment_frontend_views.ScenarioCreateView.as_view()),
    path('api/experiment/', experiment_frontend_views.ExperimentListView.as_view()),
    path('api/experiment/create/', experiment_frontend_views.ExperimentCreateView.as_view()),
    path('api/experiment/scenario_<str:uuid>/', experiment_frontend_views.ExperimentByScenarioListView.as_view()),


    path('api/request/scenario/', experiments_views.ScenarioRequestView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

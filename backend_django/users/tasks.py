from django.contrib.auth.models import User
from django.conf import settings
from users.models import Team, Organization
from celery import shared_task
import requests
from users.models import GiteaUser


import logging
log = logging.getLogger(__name__)


class TaskFailure(Exception):
    pass


@shared_task()
def update_teams(username: str):
    """
    retrieve teams from gitea and update the user's profile (add or remove teams)
    :param username:
    :return:
    """
    # get user
    user = User.objects.get(username=username)
    # get teams from gitea
    social_account = user.socialaccount_set.first()
    if not social_account:
        raise TaskFailure(f'No social account found for user {username}')
    social_token = social_account.socialtoken_set.first()
    if not social_token:
        raise TaskFailure(f'No social token found for user {username}')
    token = social_token.token
    if not token:
        log.error(f'could not get token for user {username}')
        raise TaskFailure(f'could not get token for user {username}')
    teams_api_url = f'{settings.GITEA_API}user/teams'
    resp = requests.get(teams_api_url,
                        headers={'Authorization': f'Bearer {token}'})
    if resp.status_code == 200:
        data = resp.json()
        log.warning(f'got teams from gitea: {data}')

        for team_data in data:
            # get or create organization
            try:
                organization = Organization.objects.get(gitea_id=team_data['organization']['id'])
            except Organization.DoesNotExist:
                organization = None

            if not organization:
                organization = Organization(gitea_id=team_data['organization']['id'],
                                            name=team_data['organization']['name'],
                                            description=team_data['organization']['description'],
                                            avatar=team_data['organization']['avatar_url'])
                organization.save()
                log.info(f'created organization {organization.name}')
            else:
                # update organization
                organization.name = team_data['organization']['name']
                organization.description = team_data['organization']['description']
                organization.avatar = team_data['organization']['avatar_url']
                organization.save()

            # get or create team
            try:
                team = Team.objects.get(gitea_id=team_data['id'])
            except Team.DoesNotExist:
                team = None

            if not team:
                team = Team(gitea_id=team_data['id'],
                            name=team_data['name'],
                            description=team_data['description'],
                            organization=organization)
                team.save()
                log.info(f'created team {team.name}')
            else:
                # update team
                team.name = team_data['name']
                team.description = team_data['description']
                team.organization = organization
                team.save()

            user.profile.teams.add(team)
            user.profile.save()

        # remove teams which are not in gitea anymore
        for team in user.profile.teams.all():
            if team.gitea_id not in [team_data['id'] for team_data in data]:
                user.profile.teams.remove(team)
                user.profile.save()
                log.info(f'removed team {team.name}')

    else:
        log.error(f'could not get teams from gitea: {resp.status_code}')
        raise TaskFailure(f'could not get teams from gitea: {resp.status_code} {teams_api_url} {token}')


@shared_task()
def update_gitea_user(django_user_id: int, gitea_user_id: int, username: str, email: str, avatar: str):
    user = User.objects.get(id=django_user_id)
    # get or create gitea user
    gitea_user = GiteaUser.objects.filter(gitea_id=gitea_user_id).first()
    if not gitea_user:
        gitea_user = GiteaUser(gitea_id=gitea_user_id, username=username, email=email)
    else:
        gitea_user.email = email
        gitea_user.username = username
    gitea_user.avatar = avatar
    gitea_user.user = user
    gitea_user.save()

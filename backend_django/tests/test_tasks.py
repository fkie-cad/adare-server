import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User

from users.models import GiteaUser
from users.tasks import update_gitea_user, update_teams, TaskFailure
from tests.factories import UserFactory, GiteaUserFactory


@pytest.mark.django_db
class TestUpdateGiteaUser:

    def test_creates_new_gitea_user(self):
        user = UserFactory()
        update_gitea_user(
            django_user_id=user.id,
            gitea_user_id=12345,
            username=user.username,
            email=user.email,
            avatar='https://example.com/avatar.png',
        )
        gu = GiteaUser.objects.get(gitea_id=12345)
        assert gu.username == user.username
        assert gu.user == user
        assert gu.avatar == 'https://example.com/avatar.png'

    def test_updates_existing_gitea_user(self):
        gu = GiteaUserFactory(gitea_id=99999)
        old_email = gu.email
        update_gitea_user(
            django_user_id=gu.user.id,
            gitea_user_id=99999,
            username='new-username',
            email='new@test.local',
            avatar='https://example.com/new-avatar.png',
        )
        gu.refresh_from_db()
        assert gu.username == 'new-username'
        assert gu.email == 'new@test.local'
        assert gu.avatar == 'https://example.com/new-avatar.png'


@pytest.mark.django_db
class TestUpdateTeams:

    def test_missing_social_account_raises(self):
        user = UserFactory()
        with pytest.raises(TaskFailure, match='No social account'):
            update_teams(user.username)

    def test_missing_social_token_raises(self):
        from allauth.socialaccount.models import SocialAccount
        user = UserFactory()
        SocialAccount.objects.create(
            user=user,
            provider='gitea',
            uid='123',
        )
        with pytest.raises(TaskFailure, match='No social token'):
            update_teams(user.username)

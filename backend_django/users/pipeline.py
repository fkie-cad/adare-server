from users.models import Profile
from django.contrib.auth.models import User

import logging
log = logging.getLogger(__name__)


def update_user_social_data(strategy, *args, **kwargs):
    # get user with username
    username = kwargs['response']['login']
    user = User.objects.get(username=username)
    print(kwargs['response']['avatar_url'])
    # get profile
    if not user.profile:
        profile = Profile.objects.create(user=user)
        if 'avatar_url' in kwargs['response']:
            profile.avatar = kwargs['response']['avatar_url']
        profile.save()
        log.info('Created profile for user: ' + user.username)
    else:
        # check if avatar is different
        profile = user.profile
        if 'avatar_url' in kwargs['response']:
            if profile.avatar != kwargs['response']['avatar_url']:
                profile.avatar = kwargs['response']['avatar_url']
                profile.save()
                log.info('Updated avatar for user: ' + user.username)


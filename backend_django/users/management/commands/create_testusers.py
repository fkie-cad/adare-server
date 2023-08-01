from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


import logging
log = logging.getLogger(__name__)


USERS = {
    'testuser1_none': [],
    'testuser2_supervisor': ['supervisor'],
    'testuser3_admin': ['admin'],
    'testuser4_supervisor_admin': ['supervisor', 'admin'],
    'testuser5_supervisor': ['supervisor'],
    'testuser6_supervisor': ['supervisor'],
    'testuser7_supervisor': ['supervisor'],
    'testuser8_supervisor': ['supervisor'],
    'testuser9_supervisor': ['supervisor'],
}


class Command(BaseCommand):
    help = 'Creates test users'

    def handle(self, *args, **options):
        for user, groups in USERS.items():
            # try to get user

            new_user_query = User.objects.filter(username=user)
            if new_user_query:
                new_user = User.objects.get(username=user)
                msg = f'user {user} already exists'
                log.debug(msg)
                print(msg)
            else:
                new_user = User.objects.create_user(username=user, password='test', email=f'{user}@email.com')
                msg = f'user {user} created'
                log.info(msg)
                print(msg)
            for group in groups:
                if group == 'admin':
                    new_user.is_staff = True
                    new_user.is_superuser = True
                    new_user.save()
                    log.info(f'user {user} is now admin')
                    print(f'user {user} is now admin')
                else:
                    group_query = Group.objects.filter(name=group)
                    if group_query:
                        group_obj = Group.objects.get(name=group)
                        new_user.groups.add(group_obj)
                        log.info(f'user {user} added to group {group}')
                        print(f'user {user} added to group {group}')
                    else:
                        log.error(f'group {group} does not exist')
                        print(f'group {group} does not exist')

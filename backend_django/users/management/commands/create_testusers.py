from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from setup.predefined import USERS


import logging
log = logging.getLogger(__name__)

# USERS have the following format:
# USERS = [
#     {
#         'username': $USERNAME,
#         'groups': [$GROUP1, $GROUP2, ...],
#         'password': $PASSWORD,
#         'email': $EMAIL,
#     }


class Command(BaseCommand):
    help = 'Creates test users'

    def handle(self, *args, **options):
        for user_entry in USERS:
            # try to get user
            username = user_entry['username']
            groups = user_entry['groups']
            password = user_entry['password']
            email = user_entry['email']
            new_user_query = User.objects.filter(username=username)
            if new_user_query:
                new_user = User.objects.get(username=username)
                msg = f'user {username} already exists'
                log.debug(msg)
                print(msg)
            else:
                new_user = User.objects.create_user(username=username, password=password, email=email)
                msg = f'user {username} created'
                log.info(msg)
                print(msg)
            for group in groups:
                if group == 'admin':
                    new_user.is_staff = True
                    new_user.is_superuser = True
                    new_user.save()
                    log.info(f'user {username} is now admin')
                    print(f'user {username} is now admin')
                else:
                    group_query = Group.objects.filter(name=group)
                    if group_query:
                        group_obj = Group.objects.get(name=group)
                        new_user.groups.add(group_obj)
                        log.info(f'user {username} added to group {group}')
                        print(f'user {username} added to group {group}')
                    else:
                        log.error(f'group {group} does not exist')
                        print(f'group {group} does not exist')

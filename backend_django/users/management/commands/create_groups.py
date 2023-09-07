from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from setup.predefined import GROUPS

import logging
log = logging.getLogger(__name__)

# GROUPS have the following format:
# GROUPS = [
#     $GROUP1,
#     $GROUP2,
#     ...
# ]


class Command(BaseCommand):
    help = 'Creates groups'

    def handle(self, *args, **options):
        for group in GROUPS:
            new_group, created = Group.objects.get_or_create(name=group)
            if created:
                msg = f'Group {group} created'
                log.info(msg)
            else:
                msg = f'Group {group} already exists'
                log.debug(msg)
            print(msg)

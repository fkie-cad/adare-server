from django.core.management.base import BaseCommand

from users.achievements import evaluate_achievements
from users.models import Profile


class Command(BaseCommand):
    help = 'Evaluate achievements for all users (or a specific user)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Evaluate achievements for a specific user only',
        )

    def handle(self, *args, **options):
        username = options.get('username')

        if username:
            try:
                profile = Profile.objects.get(user__username=username)
            except Profile.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'User "{username}" not found'))
                return
            profiles = [profile]
        else:
            profiles = Profile.objects.select_related('user').all()

        for profile in profiles:
            self.stdout.write(f'Evaluating achievements for {profile.user.username}...')
            evaluate_achievements(profile)

        self.stdout.write(self.style.SUCCESS('Done.'))

import logging

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from users.models import Profile

log = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender='experiments.ExperimentRun')
def evaluate_achievements_on_run(sender, instance, created, **kwargs):
    if not created:
        return
    from users.achievements import evaluate_achievements, _get_profile_for_gitea_user
    profile = _get_profile_for_gitea_user(instance.published_by)
    if profile:
        evaluate_achievements(profile)


@receiver(post_save, sender='experiments.Experiment')
def evaluate_achievements_on_experiment(sender, instance, **kwargs):
    if not instance.published:
        return
    from users.achievements import evaluate_achievements, _get_profile_for_gitea_user
    profile = _get_profile_for_gitea_user(instance.created_by)
    if profile:
        evaluate_achievements(profile)

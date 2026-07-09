import logging

from users.models import AchievementDefinition, UserAchievement, Profile

log = logging.getLogger(__name__)


def _get_profile_for_gitea_user(gitea_user):
    """Bridge GiteaUser -> User -> Profile. Returns None if unlinked."""
    if gitea_user is None or gitea_user.user is None:
        return None
    try:
        return gitea_user.user.profile
    except Profile.DoesNotExist:
        return None


def _count_published_experiments(profile):
    from experiments.models import Experiment
    return Experiment.objects.filter(
        published=True,
        created_by__user=profile.user,
    ).count()


def _count_published_runs(profile):
    from experiments.models import ExperimentRun
    return ExperimentRun.objects.filter(
        published_by__user=profile.user,
    ).count()


def _count_successful_runs(profile):
    from experiments.models import ExperimentRun
    return ExperimentRun.objects.filter(
        published_by__user=profile.user,
        result_status__name='success',
    ).count()


def _count_distinct_experiments_run(profile):
    from experiments.models import ExperimentRun
    return ExperimentRun.objects.filter(
        published_by__user=profile.user,
    ).values('experiment').distinct().count()


def _count_distinct_environments_run(profile):
    from experiments.models import ExperimentRun
    return ExperimentRun.objects.filter(
        published_by__user=profile.user,
    ).values('environment').distinct().count()


def check_first_experiment(profile):
    count = _count_published_experiments(profile)
    return count >= 1, count


def check_experiment_veteran(profile):
    count = _count_published_experiments(profile)
    return count >= 10, count


def check_first_run(profile):
    count = _count_published_runs(profile)
    return count >= 1, count


def check_run_century(profile):
    count = _count_published_runs(profile)
    return count >= 100, count


def check_first_success(profile):
    count = _count_successful_runs(profile)
    return count >= 1, count


def check_experimenter(profile):
    count = _count_distinct_experiments_run(profile)
    return count >= 5, count


def check_multi_environment(profile):
    count = _count_distinct_environments_run(profile)
    return count >= 5, count


CHECKERS = {
    'first_experiment': check_first_experiment,
    'experiment_veteran': check_experiment_veteran,
    'first_run': check_first_run,
    'run_century': check_run_century,
    'first_success': check_first_success,
    'experimenter': check_experimenter,
    'multi_environment': check_multi_environment,
}


def evaluate_achievements(profile):
    """Evaluate all achievements for a profile, creating/updating UserAchievements."""
    for definition in AchievementDefinition.objects.all():
        checker = CHECKERS.get(definition.slug)
        if checker is None:
            continue

        should_award, count = checker(profile)
        if should_award:
            achievement, created = UserAchievement.objects.get_or_create(
                profile=profile,
                definition=definition,
                defaults={'count': count},
            )
            if not created and achievement.count != count:
                achievement.count = count
                achievement.save(update_fields=['count', 'date_updated'])

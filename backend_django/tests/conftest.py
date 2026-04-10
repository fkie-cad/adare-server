import pytest
from django.core.management import call_command
from experiments.models import Status
from tests.factories import GiteaUserFactory, EnvironmentFactory, AbstractTestFactory, ExperimentFactory


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Ensure status fixture is loaded at session start."""
    with django_db_blocker.unblock():
        call_command('loaddata', 'status')


@pytest.fixture
def statuses(db):
    """Dict of status name -> Status instance."""
    return {s.name: s for s in Status.objects.all()}


@pytest.fixture
def gitea_user(db):
    return GiteaUserFactory()


@pytest.fixture
def published_experiment(db, gitea_user):
    env = EnvironmentFactory(published_by=gitea_user)
    abstract_test = AbstractTestFactory()
    exp = ExperimentFactory(
        published_by=gitea_user,
        environments=[env],
        abstract_tests=[abstract_test],
    )
    return exp

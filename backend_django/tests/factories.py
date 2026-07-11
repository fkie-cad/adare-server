import hashlib

import factory
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from experiments.models import (
    AbstractTest,
    ActionEvent,
    Environment,
    ErrorEvent,
    Experiment,
    ExperimentRun,
    Label,
    OsInfo,
    PostSetupInstallation,
    Request,
    Requirement,
    Result,
    Status,
    Tag,
    TestEvent,
    TestFunction,
    TestParameter,
    TestParameterEntry,
    TestfunctionSet,
    Tool,
    generate_ulid,
)
from users.models import GiteaUser


# ---------------------------------------------------------------------------
# Base models (no foreign keys)
# ---------------------------------------------------------------------------

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser-{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.local')


class StatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Status
        django_get_or_create = ('name',)

    name = 'success'


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    value = factory.Sequence(lambda n: f'tag-{n}')


class OsInfoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OsInfo

    os = 'Linux'
    distribution = 'Ubuntu'
    version = '22.04'
    language = 'en_US'
    architecture = 'x86_64'


class PostSetupInstallationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PostSetupInstallation

    name = factory.Sequence(lambda n: f'install-{n}')
    command = 'apt install test'


class ToolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tool

    name = factory.Sequence(lambda n: f'tool-{n}')
    command = 'echo test'


class TestParameterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestParameter

    name = factory.Sequence(lambda n: f'param-{n}')
    dtype = 'string'


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Label

    gitea_label_id = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f'label-{n}')
    color = 'ff0000'


# ---------------------------------------------------------------------------
# User factories
# ---------------------------------------------------------------------------

class GiteaUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GiteaUser

    user = factory.SubFactory(UserFactory)
    gitea_id = factory.Sequence(lambda n: 10000 + n)
    username = factory.LazyAttribute(lambda o: o.user.username)
    email = factory.LazyAttribute(lambda o: o.user.email)


# ---------------------------------------------------------------------------
# Model factories (with foreign keys)
# ---------------------------------------------------------------------------

class EnvironmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Environment

    ulid = factory.LazyFunction(generate_ulid)
    name = factory.Sequence(lambda n: f'test-env-{n}')
    vagrantbox = 'generic/ubuntu2204'
    os_info = factory.SubFactory(OsInfoFactory)
    file = 'http://gitea/api/v1/repos/test/repo/raw/env.yml?ref=main'
    sha256hash = factory.Sequence(lambda n: hashlib.sha256(f'env-{n}'.encode()).hexdigest())
    published_by = factory.SubFactory(GiteaUserFactory)
    created_by = factory.SelfAttribute('published_by')
    published = True
    published_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.add(*extracted)

    @factory.post_generation
    def post_setup_installations(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.post_setup_installations.add(*extracted)


class RequirementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Requirement

    package = factory.Sequence(lambda n: f'package-{n}')
    version = '1.0'
    relation = '>='


class TestfunctionSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestfunctionSet

    ulid = factory.LazyFunction(generate_ulid)
    name = factory.Sequence(lambda n: f'test-tfset-{n}')
    file = 'http://gitea/api/v1/repos/test/repo/raw/tf.py?ref=main'
    requirements_file = 'http://gitea/api/v1/repos/test/repo/raw/requirements.txt?ref=main'
    sha256hash = factory.Sequence(lambda n: hashlib.sha256(f'tfset-{n}'.encode()).hexdigest())
    sha256testfunctionset = factory.Sequence(lambda n: hashlib.sha256(f'tf-{n}'.encode()).hexdigest())
    sha256requirements = factory.Sequence(lambda n: hashlib.sha256(f'req-{n}'.encode()).hexdigest())
    published_by = factory.SubFactory(GiteaUserFactory)
    created_by = factory.SelfAttribute('published_by')
    published = True
    published_at = factory.LazyFunction(timezone.now)


class TestFunctionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestFunction

    testfunction_set = factory.SubFactory(TestfunctionSetFactory)
    name = factory.Sequence(lambda n: f'test-func-{n}')
    type = 'IsFile'

    @factory.post_generation
    def possible_parameters(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.possible_parameters.add(*extracted)


class TestParameterEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestParameterEntry

    parameter = factory.SubFactory(TestParameterFactory)
    value = 'test-value'


class AbstractTestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AbstractTest

    ulid = factory.LazyFunction(generate_ulid)
    name = factory.Sequence(lambda n: f'abstract-test-{n}')
    testfunction = factory.SubFactory(TestFunctionFactory)

    @factory.post_generation
    def parameters(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.parameters.add(*extracted)


class ExperimentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Experiment

    ulid = factory.LazyFunction(generate_ulid)
    name = factory.Sequence(lambda n: f'test-experiment-{n}')
    sha256hash = factory.Sequence(lambda n: hashlib.sha256(f'exp-{n}'.encode()).hexdigest())
    playbook_file = 'http://gitea/api/v1/repos/test/repo/raw/playbook.yml?ref=main'
    metadata_file = 'http://gitea/api/v1/repos/test/repo/raw/metadata.yml?ref=main'
    published_by = factory.SubFactory(GiteaUserFactory)
    created_by = factory.SelfAttribute('published_by')
    published = True
    published_at = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def environments(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.environments.add(*extracted)

    @factory.post_generation
    def abstract_tests(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.abstract_tests.add(*extracted)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.add(*extracted)


class ResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Result

    status = factory.SubFactory(StatusFactory, name='success')
    details = ''


class ExperimentRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExperimentRun

    ulid = factory.LazyFunction(generate_ulid)
    experiment = factory.SubFactory(ExperimentFactory)
    environment = factory.LazyAttribute(
        lambda o: o.experiment.environments.first() or EnvironmentFactory()
    )
    status = factory.SubFactory(StatusFactory, name='finished')
    result_status = factory.SubFactory(StatusFactory, name='success')
    published_by = factory.SelfAttribute('experiment.published_by')
    published_at = factory.LazyFunction(timezone.now)
    timestamp_start = factory.LazyFunction(timezone.now)
    timestamp_end = factory.LazyFunction(timezone.now)
    content_hash = factory.Sequence(lambda n: f'hash-{n}')
    adarevm_logfile = factory.django.FileField(filename='adarevm.log', data=b'test log content')


# ---------------------------------------------------------------------------
# Event factories
# ---------------------------------------------------------------------------

class ActionEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActionEvent

    ulid = factory.LazyFunction(generate_ulid)
    run = factory.SubFactory(ExperimentRunFactory)
    status = factory.SubFactory(StatusFactory, name='finished')
    category = 'command'
    error = ''
    event_group_id = factory.Sequence(lambda n: str(n))
    timestamp = factory.LazyFunction(timezone.now)
    action_type = 'command'
    action_id = 'test-cmd'
    action_data = '{"command": "echo hello", "returncode": 0, "stdout": "hello"}'


class TestEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TestEvent

    ulid = factory.LazyFunction(generate_ulid)
    run = factory.SubFactory(ExperimentRunFactory)
    status = factory.SubFactory(StatusFactory, name='finished')
    category = 'test'
    error = ''
    event_group_id = factory.Sequence(lambda n: str(n))
    timestamp = factory.LazyFunction(timezone.now)
    abstracttest = factory.SubFactory(AbstractTestFactory)
    result = factory.SubFactory(ResultFactory)


class ErrorEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ErrorEvent

    ulid = factory.LazyFunction(generate_ulid)
    run = factory.SubFactory(ExperimentRunFactory)
    status = factory.SubFactory(StatusFactory, name='finished')
    category = 'error'
    error = ''
    event_group_id = factory.Sequence(lambda n: str(n))
    timestamp = factory.LazyFunction(timezone.now)
    error_name = 'TestError'
    error_msg = 'Something went wrong'


# ---------------------------------------------------------------------------
# Request factory
# ---------------------------------------------------------------------------

class RequestObjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Request

    ulid = factory.LazyFunction(generate_ulid)
    title = factory.Sequence(lambda n: f'Request {n}')
    description = 'Test request'
    creation_date = factory.LazyFunction(timezone.now)
    last_change_date = factory.LazyFunction(timezone.now)
    gitea_pr_url = factory.Sequence(lambda n: f'http://gitea/pr/{n}')
    gitea_pr_number = factory.Sequence(lambda n: n + 100)
    gitea_pr_status = 'open'
    action = 'create'
    objective_name = 'experiment'
    objective = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(Experiment)
    )
    object_id = factory.LazyAttribute(lambda o: ExperimentFactory().ulid)
    requester = factory.SubFactory(GiteaUserFactory)

    @factory.post_generation
    def reviewers(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.reviewers.add(*extracted)

    @factory.post_generation
    def assignees(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.assignees.add(*extracted)

    @factory.post_generation
    def labels(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.labels.add(*extracted)

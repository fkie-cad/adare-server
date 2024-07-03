from django.db import models
import ulid
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from users.models import GiteaUser


def generate_ulid():
    return str(ulid.ULID())


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return str(self.name)


class Status(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.name)


class Result(models.Model):
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    details = models.CharField(max_length=2000, blank=True)

    def __str__(self):
        return str(self.status)


class TestParameter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dtype = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return str(self.name)


class TestParameterEntry(models.Model):
    parameter = models.ForeignKey(TestParameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=2000)

    def __str__(self):
        return str(self.parameter)


class Event(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)

    category = models.CharField(max_length=100)

    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    error = models.CharField(max_length=2000, blank=True)
    group_id = models.IntegerField()

    timestamp = models.DateTimeField()

    class Meta:
        abstract = True


class CommandEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='command_events')
    name = models.CharField(max_length=100)
    command = models.CharField(max_length=2000)
    returncode = models.IntegerField()
    stdout = models.TextField(blank=True)


class TestEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='test_events')
    abstracttest = models.ForeignKey('AbstractTest', on_delete=models.CASCADE)
    result = models.ForeignKey(Result, on_delete=models.PROTECT)


class ErrorEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='error_events')
    error_name = models.CharField(max_length=100)
    error_msg = models.CharField(max_length=2000)


class GuiFindEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='gui_find_events')
    text = models.BooleanField()
    objective = models.CharField(max_length=1000)
    success = models.IntegerField()


class GuiClickEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='gui_click_events')
    clicktype = models.CharField(max_length=100)
    modifiers = models.CharField(max_length=100)
    target = models.CharField(max_length=1000)


class GuiKeypressEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='gui_keypress_events')
    keys = models.CharField(max_length=1000)


class GuiIdleEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='gui_idle_events')
    seconds = models.IntegerField()


# class Stage(models.Model):
#     id = models.IntegerField(primary_key=True, auto_created=True)
#     name = models.CharField(max_length=100, unique=True)
#     msg = models.CharField(max_length=1000, blank=True)
#     description = models.CharField(max_length=10000, blank=True)
#     optional = models.BooleanField(default=False)
#     parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
#
#     @property
#     def level(self):
#         if self.parent:
#             return self.parent.level + 1
#         return 0
#
#
# class StageInRun(models.Model):
#     id = models.IntegerField(primary_key=True, auto_created=True)
#     stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
#
#     run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE)
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     status = models.ForeignKey(Status, on_delete=models.PROTECT)
#     sub_msg = models.CharField(max_length=1000, blank=True)
#     result_status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='result_status', blank=True, null=True)


class Requirement(models.Model):
    package = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=100, blank=True)
    relation = models.CharField(max_length=100, blank=True)


class TestfunctionSet(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=1000, blank=True)
    requirements = models.ManyToManyField(Requirement)
    file = models.URLField(max_length=2000)
    sha256hash = models.CharField(max_length=64, unique=True)
    sha256testfunctionset = models.CharField(max_length=64)
    sha256requirements = models.CharField(max_length=64)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='testfunctionsets_published')
    accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='testfunctionsets_accepted',
                                    blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)


class TestFunction(models.Model):
    # test name e.g. is_file
    name = models.CharField(max_length=100)
    # test type (class name) e.g. IsFile
    type = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    possible_parameters = models.ManyToManyField(TestParameter)
    testfunction_set = models.ForeignKey(TestfunctionSet, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'testfunction_set'], name='unique_testfunction')
        ]

    def __str__(self):
        return str(self.name)


class Tool(models.Model):
    name = models.CharField(max_length=50)
    command = models.CharField(max_length=200)

    def __str__(self):
        return str(self.name)


class AbstractTest(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)
    testfunction = models.ForeignKey(TestFunction, on_delete=models.CASCADE)
    parameters = models.ManyToManyField(TestParameterEntry)
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return str(self.name)


# class Test(models.Model):
#     ulid = models.CharField(primary_key=True, max_length=26, default=lambda: generate_ulid)
#     abstracttest = models.ForeignKey(AbstractTest, on_delete=models.CASCADE)
#     result = models.ForeignKey(Result, on_delete=models.CASCADE)
#
#     def __str__(self):
#         return str(self.abstracttest.name)


class OsInfo(models.Model):
    os = models.CharField(max_length=50)
    distribution = models.CharField(max_length=50)
    version = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    architecture = models.CharField(max_length=50, blank=True, null=True)
    details = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.os} - {self.distribution} {self.version} ({self.language, self.architecture})'


class PostSetupInstallation(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=1000, blank=True)
    command = models.CharField(max_length=2000)


class Environment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    vagrantbox = models.URLField(max_length=2000)
    description = models.CharField(max_length=1000, blank=True, null=True)
    os_info = models.ForeignKey(OsInfo, on_delete=models.PROTECT)
    post_setup_installations = models.ManyToManyField(PostSetupInstallation)
    file = models.URLField(max_length=2000)
    tags = models.ManyToManyField(Tag)

    sha256hash = models.CharField(max_length=64, unique=True)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='environments_published')
    accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='environments_accepted',
                                    blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'


class Experiment(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)

    action_file = models.URLField(max_length=2000)
    testset_file = models.URLField(max_length=2000)
    metadata_file = models.URLField(max_length=2000)
    bibtex_file = models.URLField(max_length=2000, blank=True, null=True)
    markdown_file = models.URLField(max_length=2000, blank=True, null=True)

    environments = models.ManyToManyField(Environment)
    abstract_tests = models.ManyToManyField(AbstractTest)
    tags = models.ManyToManyField(Tag)

    sha256hash = models.CharField(max_length=64, unique=True)
    sha256action = models.CharField(max_length=64)
    sha256testset = models.CharField(max_length=64)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='experiments_published')
    accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='experiments_accepted',
                                    blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'


class ExperimentRun(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT)
    published_at = models.DateTimeField()
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='experiment_runs')
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)
    timestamp_start = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    status = models.ForeignKey(Status, on_delete=models.PROTECT)

    logfile = models.FileField(upload_to='logfiles/')

    def __str__(self):
        return f'{self.ulid}'

    @property
    def events(self):
        event_classes = [CommandEvent, TestEvent, ErrorEvent, GuiFindEvent, GuiClickEvent, GuiKeypressEvent,
                         GuiIdleEvent]
        events = [
            event for event_class in event_classes for event in event_class.objects.filter(run=self)
        ]
        return events


# class Scenario(models.Model):
#     ulid = models.CharField(primary_key=True, max_length=26, default=lambda: generate_ulid)
#     name = models.CharField(max_length=100, unique=True)
#     experiments = models.ManyToManyField(Experiment, related_name='scenarios', blank=True)
#     description = models.CharField(max_length=1000, blank=True)
#     tags = models.ManyToManyField(Tag, blank=True)
#
#     published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='scenarios_published')
#     accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='scenarios_accepted', blank=True,
#                                     null=True)
#     published_at = models.DateTimeField(blank=True, null=True)
#     published = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f'{self.name}'


class Label(models.Model):
    gitea_label_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=6)
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return str(self.name)


class Request(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    title = models.CharField(max_length=1000)
    description = models.CharField(max_length=3000, blank=True)

    creation_date = models.DateTimeField()
    last_change_date = models.DateTimeField()

    gitea_pr_url = models.URLField(max_length=2000, blank=True)
    gitea_pr_number = models.IntegerField(blank=True, unique=True)
    gitea_pr_status = models.CharField(max_length=20, blank=True)

    action = models.CharField(max_length=100, null=False, blank=False)

    # generic foreign key to the object the request is about (e.g. Experiment, Scenario)
    objective_name = models.CharField(max_length=100)
    objective = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=26)
    object = GenericForeignKey('objective', 'object_id')

    # for action 'modify' we additionally need to store the old object
    old_objective_name = models.CharField(max_length=100, null=True, blank=True)
    old_objective = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='old_objective', null=True,
                                      blank=True)
    old_object_id = models.CharField(max_length=26, null=True, blank=True)
    old_object = GenericForeignKey('old_objective', 'old_object_id')

    requester = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='requests')

    reviewers = models.ManyToManyField(GiteaUser, related_name='requests_reviewing', blank=True)
    assignees = models.ManyToManyField(GiteaUser, related_name='requests_assigned', blank=True)

    labels = models.ManyToManyField(Label, blank=True)

    @property
    def assigned(self):
        return self.assignees.exists()

    def __str__(self):
        return f'{self.title} - {self.gitea_pr_status}'


class RequestCreationMessage(models.Model):
    gitea_pr_number = models.IntegerField(primary_key=True)
    error_message = models.CharField(max_length=2000, blank=True)

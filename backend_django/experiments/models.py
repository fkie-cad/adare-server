from django.db import models
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import GiteaUser


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


class Requirement(models.Model):
    package = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=100, blank=True)
    relation = models.CharField(max_length=100, blank=True)


class TestfunctionSet(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=1000, blank=True)
    requirements = models.ManyToManyField(Requirement)
    sha256hash = models.CharField(max_length=64, unique=True)
    sha256testfunctionset = models.CharField(max_length=64)
    sha256requirements = models.CharField(max_length=64)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='testfunctionsets_published')
    accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='testfunctionsets_accepted', blank=True, null=True)
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
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)
    testfunction = models.ForeignKey(TestFunction, on_delete=models.CASCADE)
    parameters = models.ManyToManyField(TestParameterEntry)
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Test(models.Model):
    uuid = models.UUIDField(primary_key=True)
    abstracttest = models.ForeignKey(AbstractTest, on_delete=models.CASCADE)
    result = models.ForeignKey(Result, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.abstracttest.name)


class OsInfo(models.Model):
    os = models.CharField(max_length=50)
    distribution = models.CharField(max_length=50)
    version = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=50, blank=True)
    architecture = models.CharField(max_length=50, blank=True)
    details = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.os} - {self.distribution} {self.version} ({self.language, self.architecture})'


class Experiment(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)

    action_file = models.URLField(max_length=2000)
    testset_file = models.URLField(max_length=2000)
    os_file = models.URLField(max_length=2000)

    os_info = models.ForeignKey(OsInfo, on_delete=models.PROTECT)
    abstract_tests = models.ManyToManyField(AbstractTest)
    tags = models.ManyToManyField(Tag)

    sha256hash = models.CharField(max_length=64, unique=True)
    sha256action = models.CharField(max_length=64, unique=True)
    sha256testset = models.CharField(max_length=64, unique=True)
    sha256os = models.CharField(max_length=64, unique=True)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='experiments_published')
    accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='experiments_accepted', blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'


class ExperimentRun(models.Model):
    uuid = models.UUIDField(primary_key=True)
    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT)
    published_at = models.DateTimeField()
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='experiment_runs')
    timestamp_start = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    tests = models.ManyToManyField(Test)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)

    logfile = models.FileField(upload_to='logfiles/')

    def __str__(self):
        return f'{self.uuid}'


class Scenario(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, unique=True)
    experiments = models.ManyToManyField(Experiment, related_name='scenarios', blank=True)
    description = models.CharField(max_length=1000, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='scenarios_published')
    accepted_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='scenarios_accepted', blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'


class Label(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.name)


class Request(models.Model):
    title = models.CharField(max_length=1000)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    description = models.CharField(max_length=3000, blank=True)

    creation_date = models.DateTimeField()
    last_change_date = models.DateTimeField()

    gitea_pr_url = models.URLField(max_length=2000, blank=True)
    gitea_pr_number = models.IntegerField(blank=True, unique=True)
    gitea_pr_status = models.CharField(max_length=20, blank=True)

    action = models.CharField(max_length=100, null=False, blank=False)

    # generic foreign key to the object the request is about (e.g. Experiment, Scenario)
    objective = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('objective', 'object_id')

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

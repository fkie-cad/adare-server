from django.db import models
from django.contrib.auth.models import User
import uuid


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

    def __str__(self):
        return str(self.name)


class TestParameterEntries(models.Model):
    parameter = models.ForeignKey(TestParameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=2000)

    def __str__(self):
        return str(self.parameter)


class TestFunction(models.Model):
    name = models.CharField(max_length=100, unique=True)
    test_name = models.CharField(max_length=100, unique=True)
    test_description = models.CharField(max_length=1000, blank=True)
    possible_parameters = models.ManyToManyField(TestParameter)

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
    parameters = models.ManyToManyField(TestParameterEntries)
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, null=True)

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
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500, blank=True)
    publisher = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    publish_date = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    abstract_tests = models.ManyToManyField(AbstractTest)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return f'{self.name}'


class ExperimentRun(models.Model):
    uuid = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='scenario_runs')
    timestamp_start = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    tests = models.ManyToManyField(Test)
    description = models.CharField(max_length=500, blank=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.uuid}'


class Scenario(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, unique=True)
    publisher = models.ForeignKey(User, on_delete=models.PROTECT)
    publish_date = models.DateTimeField()
    experiments = models.ManyToManyField(Experiment, related_name='experiments', blank=True)
    description = models.CharField(max_length=1000, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f'{self.name}'


class RequestStatus(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.name)


class Label(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.name)


class Request(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    last_changed = models.DateTimeField()

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, blank=True, null=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, blank=True, null=True)

    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    supervisor = models.ForeignKey(User, related_name='requests_assigned', blank=True, on_delete=models.PROTECT)
    supervisor_assigned_by = models.ForeignKey(User, related_name='requests_assigned_by', blank=True, on_delete=models.PROTECT)
    status = models.ForeignKey(RequestStatus, on_delete=models.PROTECT)
    labels = models.ManyToManyField(Label, blank=True)
    description = models.CharField(max_length=3000, blank=True)

    def __str__(self):
        return f'{self.scenario.name} - {self.requestor} - {self.status}'

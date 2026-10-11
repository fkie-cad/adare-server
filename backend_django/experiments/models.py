import itertools

from django.db import models
import ulid
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from users.models import GiteaUser


def generate_ulid():
    return str(ulid.ULID())


class TagScope(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_predefined = models.BooleanField(default=False)
    color = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return str(self.name)


class Tag(models.Model):
    scope = models.ForeignKey(TagScope, on_delete=models.SET_NULL, null=True, blank=True, related_name='tags')
    value = models.CharField(max_length=100)
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['scope', 'value'], name='unique_scope_value')
        ]

    def save(self, *args, **kwargs):
        if self.scope:
            self.name = f'{self.scope.name}:{self.value}'
        else:
            self.name = self.value
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)


class Status(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.name)


class Result(models.Model):
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    details = models.CharField(max_length=5000, blank=True)

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

    success = models.BooleanField(null=True, blank=True)
    event_group_id = models.CharField(max_length=100, blank=True, default='')
    event_type_specific = models.CharField(max_length=100, blank=True, default='')
    execution_time = models.IntegerField(null=True, blank=True)
    parent_event = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        abstract = True


class TestEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='test_events')
    abstracttest = models.ForeignKey('AbstractTest', on_delete=models.CASCADE)
    result = models.ForeignKey(Result, on_delete=models.PROTECT, blank=True, null=True)


class ErrorEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='error_events')
    error_name = models.CharField(max_length=100, blank=True, default='')
    error_msg = models.CharField(max_length=2000, blank=True, default='')


class ActionEvent(Event):
    run = models.ForeignKey('ExperimentRun', on_delete=models.CASCADE, related_name='action_events')
    action_type = models.CharField(max_length=100, blank=True, default='')
    action_id = models.CharField(max_length=100, blank=True, default='')
    action_data = models.TextField(blank=True, default='')


class Requirement(models.Model):
    package = models.CharField(max_length=100)
    version = models.CharField(max_length=100, blank=True)
    relation = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['package', 'version'], name='unique_package_version')
        ]


class TestfunctionSet(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    # not unique: a modify PR draft (published=False) may coexist with the
    # published object under the same name; sha256hash enforces content uniqueness.
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    requirements = models.ManyToManyField(Requirement)
    tags = models.ManyToManyField(Tag, blank=True)
    file = models.URLField(max_length=2000)
    requirements_file = models.URLField(max_length=2000)
    sha256hash = models.CharField(max_length=64, unique=True)
    sha256testfunctionset = models.CharField(max_length=64)
    sha256requirements = models.CharField(max_length=64)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='testfunctionsets_published_by')
    created_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='testfunctionsets_created_by', blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False, db_index=True)

    version = models.PositiveIntegerField(default=1)
    # the current version for this name; flips in lockstep with `published` at
    # merge time (see PRFinalize._publish / demote_superseded)
    is_current = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'version'], name='unique_tf_name_version'),
            models.UniqueConstraint(fields=['name'], condition=models.Q(is_current=True),
                                    name='unique_tf_current_per_name'),
        ]

    @property
    def num_testfunctions(self):
        return self.testfunctions.count()


class TestFunction(models.Model):
    # test name e.g. is_file
    name = models.CharField(max_length=100)
    # test type (class name) e.g. IsFile
    type = models.CharField(max_length=100)
    description = models.CharField(max_length=1000, blank=True)
    possible_parameters = models.ManyToManyField(TestParameter)
    testfunction_set = models.ForeignKey(TestfunctionSet, on_delete=models.CASCADE, related_name='testfunctions')

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
    repetitions = models.IntegerField(default=1)
    testfunction = models.ForeignKey(TestFunction, on_delete=models.CASCADE)
    parameters = models.ManyToManyField(TestParameterEntry)
    tools = models.ManyToManyField(Tool, blank=True)

    def __str__(self):
        return str(self.name)


class OsInfo(models.Model):
    platform = models.CharField(max_length=50, blank=True, default='')
    os = models.CharField(max_length=50)
    distribution = models.CharField(max_length=50)
    version = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    architecture = models.CharField(max_length=50, blank=True, null=True)
    details = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.os} - {self.distribution} {self.version} ({self.language, self.architecture})'


class PostSetupInstallation(models.Model):
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=1000, blank=True)
    command = models.CharField(max_length=2000)
    shell = models.BooleanField(default=False)
    cwd = models.CharField(max_length=2000, blank=True, default='')


class Recipe(models.Model):
    """Built-on-load ('tutorial') environment source: an ISO + setup params.

    Mirrors the client's `recipe:` YAML block (client-side shape lives in
    `adare/adare/adare/types/environment.py`; the ingest-side rules live in
    `giteaeventmanager/action/environment_contract.py`). One row per Environment
    (env-specific, never shared like OsInfo/PostSetupInstallation).

    Two mutually exclusive ISO forms:
      * hosted -- `iso` is an http(s) URL the consumer downloads;
      * BYO ('bring your own', Windows profiles only) -- `iso` is empty and
        `iso_name` names the bare filename the consumer must supply locally,
        because a Microsoft Windows ISO may not legally be rehosted.
    `iso_sha256` is the integrity boundary in both forms and is always set.
    """
    profile = models.CharField(max_length=200)
    # http(s) URL of the hosted ISO; empty for a BYO recipe (see iso_name).
    iso = models.CharField(max_length=2000, blank=True, default='')
    # BYO form: the bare ISO filename (no path separators) the consumer supplies
    # locally. Empty whenever `iso` is set.
    iso_name = models.CharField(max_length=200, blank=True, default='')
    # Free-text pointer telling the consumer where to obtain a BYO ISO.
    # PLAIN TEXT ONLY: this is publisher-supplied and therefore attacker-controlled
    # content -- it must never be rendered as markdown or HTML by any frontend.
    iso_notes = models.TextField(max_length=1000, blank=True, default='')
    iso_sha256 = models.CharField(max_length=64)
    template = models.CharField(max_length=200, blank=True, default='')
    setup_level = models.IntegerField(null=True, blank=True)
    disk_size = models.CharField(max_length=50, blank=True, default='')
    ram_mb = models.IntegerField(null=True, blank=True)
    cpus = models.IntegerField(null=True, blank=True)
    arch = models.CharField(max_length=50, blank=True, default='')
    # Build-time provisioning steps, stored verbatim as declared in the YAML
    # (command entries and un-expanded `for_each` groups). These run ONCE, via
    # the QEMU guest agent, while the disk image is being built -- which is what
    # makes them distinct from `Environment.post_setup_installations`, whose
    # commands run again on every experiment run.
    provision = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f'{self.profile} ({self.iso or self.iso_name})'


class Environment(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    # not unique: a modify PR draft (published=False) may coexist with the
    # published object under the same name; sha256hash enforces content uniqueness.
    # Indexed: detail/download lookup_field and the ?name= / environment_mc filters.
    name = models.CharField(max_length=100, db_index=True)
    # Modern VM source: path to an OVA disk image (client `EnvironmentMetadata.vm`),
    # or an http(s) URL for a published baked env.
    vm = models.CharField(max_length=2000, blank=True, default="")
    # sha256 of the baked disk image; required when `vm` is a published URL.
    vm_sha256 = models.CharField(max_length=64, blank=True, default="")
    # Disk image format (qcow2/ova/vmdk/vdi/img/raw); required for a `vm` URL
    # whose path has no recognizable disk extension (e.g. an owncloud share link).
    vm_format = models.CharField(max_length=10, blank=True, default='')
    # Optional install-profile provenance for a baked `vm` environment: which OS
    # profile it was built from, and (if the publisher still has it) the source
    # installer ISO's sha256. Informational only -- like `Recipe.profile`, this is
    # an unvalidated free-form value (no server-side OS-profile catalog exists to
    # check it against) and is never used to rebuild the disk. Meaningless when
    # `recipe` is set: a recipe environment already carries real build inputs.
    source_profile = models.CharField(max_length=100, blank=True, default="")
    source_iso_sha256 = models.CharField(max_length=64, blank=True, default="")
    # Legacy Vagrant source (owner/box); still valid, the frontend cloud link depends on it.
    vagrantbox = models.CharField(max_length=2000, default="")
    # Built-on-load ('tutorial') source: ISO + setup params, mutually exclusive with vm/vagrantbox.
    recipe = models.OneToOneField(Recipe, null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=1000, blank=True, null=True)
    os_info = models.ForeignKey(OsInfo, on_delete=models.PROTECT)
    post_setup_installations = models.ManyToManyField(PostSetupInstallation)
    file = models.URLField(max_length=2000)
    tags = models.ManyToManyField(Tag)

    sha256hash = models.CharField(max_length=64, unique=True)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='environments_published')
    created_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='environments_created', blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f'{self.name}'

    @property
    def vagrantbox_cloud_url(self):
        return f'https://app.vagrantup.com/{self.vagrantbox}'


class Experiment(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    # indexed: ?name= lookups (React detail page) and ingest's by-name lookup
    name = models.CharField(max_length=100, db_index=True)
    description = models.CharField(max_length=500, blank=True)

    playbook_file = models.URLField(max_length=2000, default="")
    metadata_file = models.URLField(max_length=2000)
    bibtex_file = models.URLField(max_length=2000, blank=True, null=True)
    markdown_file = models.URLField(max_length=2000, blank=True, null=True)

    environments = models.ManyToManyField(Environment)
    abstract_tests = models.ManyToManyField(AbstractTest)
    tags = models.ManyToManyField(Tag)

    sha256hash = models.CharField(max_length=64, unique=True)
    # indexed: lookup_field of the hash-to-metadata endpoint (client hash lookups)
    sha256playbook = models.CharField(max_length=64, default="", db_index=True)

    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='experiments_published')
    created_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT, related_name='experiments_created',
                                    blank=True, null=True)
    # indexed: default ordering of the experiment list
    published_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(blank=True, null=True)
    published = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f'{self.name}'


class ExperimentRun(models.Model):
    ulid = models.CharField(primary_key=True, max_length=26, default=generate_ulid)
    run_number = models.PositiveIntegerField(db_index=True, editable=False, null=True)
    published_by = models.ForeignKey(GiteaUser, on_delete=models.PROTECT)
    # indexed: default ordering of the run list
    published_at = models.DateTimeField(db_index=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='experiment_runs')
    environment = models.ForeignKey(Environment, on_delete=models.PROTECT)
    timestamp_start = models.DateTimeField(db_index=True)
    timestamp_end = models.DateTimeField()
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='status')
    result_status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='result_status')
    content_hash = models.CharField(max_length=64, blank=True, default='', db_index=True)

    adarevm_logfile = models.FileField(upload_to='logfiles/', blank=True, null=True)
    installations_logfile = models.FileField(upload_to='logfiles/', blank=True, null=True)
    packagedump_logfile = models.FileField(upload_to='logfiles/', blank=True, null=True)
    networkdrives_logfile = models.FileField(upload_to='logfiles/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Assign a per-experiment sequential run number on first insert.
        if self.run_number is None:
            self.run_number = ExperimentRun.objects.filter(experiment=self.experiment).count() + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.ulid}'

    @property
    def events(self):
        return list(itertools.chain(
            self.test_events.all(),
            self.error_events.all(),
            self.action_events.all(),
        ))


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

    class Meta:
        indexes = [
            # owning-request lookups: Request.objects.filter(objective=ct, object_id=pk)
            # (experiment check endpoints, ingest's find_owning_request)
            models.Index(fields=['objective', 'object_id'], name='request_objective_object_idx'),
        ]

    @property
    def assigned(self):
        return self.assignees.exists()

    def __str__(self):
        return f'{self.title} - {self.gitea_pr_status}'

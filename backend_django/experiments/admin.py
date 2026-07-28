from django.contrib import admin

from experiments.models import (
    Tag, TagScope, Status, Result, TestParameter, TestParameterEntry,
    TestEvent, ErrorEvent, ActionEvent, Requirement, TestfunctionSet,
    TestFunction, Tool, AbstractTest, OsInfo, PostSetupInstallation,
    Environment, Experiment, ExperimentRun, Label, Request,
)


@admin.register(TagScope)
class TagScopeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_predefined', 'color']
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'scope', 'value']
    list_filter = ['scope']
    search_fields = ['name', 'value']


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'details']
    list_filter = ['status']
    raw_id_fields = ['status']


@admin.register(TestParameter)
class TestParameterAdmin(admin.ModelAdmin):
    list_display = ['name', 'dtype']
    search_fields = ['name']


@admin.register(TestParameterEntry)
class TestParameterEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'parameter', 'value']
    raw_id_fields = ['parameter']


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['id', 'package', 'version', 'relation']
    search_fields = ['package']


@admin.register(TestfunctionSet)
class TestfunctionSetAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'name', 'version', 'is_current', 'published', 'published_by', 'published_at']
    list_filter = ['published', 'is_current']
    search_fields = ['name', 'ulid']
    raw_id_fields = ['published_by', 'created_by']


@admin.register(TestFunction)
class TestFunctionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'testfunction_set']
    search_fields = ['name']
    raw_id_fields = ['testfunction_set']


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'command']
    search_fields = ['name']


@admin.register(AbstractTest)
class AbstractTestAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'name', 'testfunction']
    search_fields = ['name', 'ulid']
    raw_id_fields = ['testfunction']


@admin.register(OsInfo)
class OsInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'os', 'distribution', 'version', 'architecture']
    list_filter = ['os', 'distribution']


@admin.register(PostSetupInstallation)
class PostSetupInstallationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'name', 'published', 'published_by', 'published_at']
    list_filter = ['published']
    search_fields = ['name', 'ulid']
    raw_id_fields = ['os_info', 'published_by', 'created_by']


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'name', 'published', 'published_by', 'published_at']
    list_filter = ['published']
    search_fields = ['name', 'ulid']
    raw_id_fields = ['published_by', 'created_by']


@admin.register(ExperimentRun)
class ExperimentRunAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'experiment', 'environment', 'status', 'result_status', 'published_at']
    list_filter = ['status', 'result_status']
    search_fields = ['ulid', 'experiment__name']
    raw_id_fields = ['published_by', 'experiment', 'environment', 'status', 'result_status']


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'color', 'gitea_label_id']
    search_fields = ['name']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'title', 'action', 'gitea_pr_status', 'requester']
    list_filter = ['gitea_pr_status', 'action']
    search_fields = ['title', 'ulid']
    raw_id_fields = ['requester', 'objective', 'old_objective']


@admin.register(TestEvent)
class TestEventAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'category', 'status', 'timestamp']
    list_filter = ['status']
    search_fields = ['ulid']
    raw_id_fields = ['run', 'status', 'abstracttest', 'result']


@admin.register(ErrorEvent)
class ErrorEventAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'error_name', 'category', 'status', 'timestamp']
    list_filter = ['status']
    search_fields = ['ulid', 'error_name']
    raw_id_fields = ['run', 'status']


@admin.register(ActionEvent)
class ActionEventAdmin(admin.ModelAdmin):
    list_display = ['ulid', 'action_type', 'category', 'status', 'timestamp']
    list_filter = ['status', 'action_type']
    search_fields = ['ulid', 'action_type', 'action_id']
    raw_id_fields = ['run', 'status']

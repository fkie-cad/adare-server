# ADARE Server Testing System Design

## Context

The ADARE server currently has zero test coverage — empty `tests.py` placeholders in every app and one manual Gitea test script (`tests/gitea_tests/pr.py`). The server manages scientific experiments with a complex lifecycle: submission via Gitea PRs, webhook-driven processing, publishing, run reporting with events, and file storage. Without tests, bugs like `ExperimentCheckView` referencing the non-existent `experiment.publish_date` go undetected. This design establishes a two-layer testing system that covers the full stack.

## Architecture

Two complementary test layers, each optimized for its purpose:

### Layer 1: pytest + Factory Boy (API Integration Tests)
- **Scope:** All REST API endpoints, serializers, filters, permissions, and edge cases
- **Data:** Factory Boy factories generate realistic model instances per-test
- **External services:** Mocked (Gitea, MinIO, Celery runs synchronously)
- **DB:** Real PostgreSQL with per-test transaction rollback (pytest-django)
- **Speed:** Seconds
- **Runner:** `make test` → `docker compose exec web python -m pytest tests/api/`

### Layer 2: Management Command (E2E Gitea Flow)
- **Scope:** Full lifecycle — submit → Gitea PR → webhook → merge → publish → run publish
- **Data:** Real files uploaded to real Gitea test repo (`adareTEST`)
- **External services:** Real Gitea server, Celery runs synchronously (`ALWAYS_EAGER`)
- **DB:** Flushed and reseeded before each run
- **Speed:** Minutes
- **Runner:** `make test-e2e` → `docker compose exec web python manage.py test_e2e_gitea`

## Directory Structure

```
backend_django/
  pytest.ini                                    # (new section in pyproject.toml)
  tests/
    __init__.py                                 # NEW
    conftest.py                                 # NEW: root fixtures (statuses, users, factories)
    factories.py                                # NEW: all Factory Boy factories
    fixtures/                                   # NEW: sample files for tests
      sample_playbook.yml
      sample_metadata.yml
      sample_testfunction.py
      sample_requirements.txt
      sample_environment.yml
      sample_logfile.txt
      webhook_payloads/                         # JSON payloads for webhook tests
        pr_opened_experiment.json
        pr_merged_experiment.json
        pr_opened_testfunction.json
        pr_merged_testfunction.json
        pr_opened_environment.json
        pr_merged_environment.json
    api/                                        # NEW: Layer 1 tests
      __init__.py
      conftest.py                               # API-specific fixtures (client, auth, mocks)
      test_experiment_endpoints.py
      test_run_endpoints.py
      test_run_publish.py
      test_environment_endpoints.py
      test_testfunction_endpoints.py
      test_request_endpoints.py
      test_stats.py
      test_submit.py
      test_webhook.py
      test_hash_endpoints.py
      test_auth.py
    gitea_tests/                                # EXISTING (unchanged)
      pr.py
    e2e/                                        # NEW: E2E helpers
      __init__.py
      gitea_cleanup.py                          # Refactored cleanup from pr.py
  experiments/
    management/
      commands/
        test_e2e_gitea.py                       # NEW: E2E management command
```

## Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-django>=4.5",
    "factory-boy>=3.3",
    "pytest-cov>=4.0",
]
```

## pytest Configuration

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "adare.settings.development"
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
markers = [
    "slow: tests that take more than 5 seconds",
]
addopts = "-v --tb=short --strict-markers"
```

## Factory Boy Factories

File: `tests/factories.py`

Factories in dependency order (each uses `factory.django.DjangoModelFactory`):

### Base Factories (no FKs)

1. **`UserFactory`** — `django.contrib.auth.models.User`
   - `username = factory.Sequence(lambda n: f'testuser-{n}')`
   - `email = factory.LazyAttribute(lambda o: f'{o.username}@test.local')`
   - Note: `Profile` auto-created by `users/signals.py` post_save signal

2. **`StatusFactory`** — `experiments.models.Status`
   - `Meta: django_get_or_create = ('name',)` (critical: uses fixture-loaded records)
   - `name = 'success'` (default)

3. **`TagFactory`** — `experiments.models.Tag`
   - `name = factory.Sequence(lambda n: f'tag-{n}')`

4. **`OsInfoFactory`** — `experiments.models.OsInfo`
   - Defaults: `os='Linux', distribution='Ubuntu', version='22.04', language='en_US', architecture='x86_64'`

5. **`PostSetupInstallationFactory`** — `experiments.models.PostSetupInstallation`

6. **`ToolFactory`** — `experiments.models.Tool`
   - `name = factory.Sequence(lambda n: f'tool-{n}')`

7. **`TestParameterFactory`** — `experiments.models.TestParameter`
   - `name = factory.Sequence(lambda n: f'param-{n}')` (must be unique)

8. **`LabelFactory`** — `experiments.models.Label`
   - `gitea_label_id = factory.Sequence(lambda n: n + 1)` (must be unique)

### User Factories

9. **`GiteaUserFactory`** — `users.models.GiteaUser`
   - `user = factory.SubFactory(UserFactory)`
   - `gitea_id = factory.Sequence(lambda n: 10000 + n)`
   - `username = factory.LazyAttribute(lambda o: o.user.username)`
   - `email = factory.LazyAttribute(lambda o: o.user.email)`

### Model Factories (with FKs)

10. **`EnvironmentFactory`** — `experiments.models.Environment`
    - `ulid = factory.LazyFunction(generate_ulid)`
    - `name = factory.Sequence(lambda n: f'test-env-{n}')`
    - `os_info = factory.SubFactory(OsInfoFactory)`
    - `sha256hash = factory.Sequence(lambda n: hashlib.sha256(f'env-{n}'.encode()).hexdigest())`
    - `published_by = factory.SubFactory(GiteaUserFactory)`
    - `created_by = factory.SelfAttribute('published_by')`
    - `published = True`, `published_at = factory.LazyFunction(timezone.now)`
    - M2M: `tags`, `post_setup_installations` via `@factory.post_generation`

11. **`RequirementFactory`** — `experiments.models.Requirement`

12. **`TestfunctionSetFactory`** — `experiments.models.TestfunctionSet`
    - Same pattern as Environment. Includes `sha256hash`, `sha256testfunctionset`, `sha256requirements`.
    - `version = 1`

13. **`TestFunctionFactory`** — `experiments.models.TestFunction`
    - `testfunction_set = factory.SubFactory(TestfunctionSetFactory)`
    - `name = factory.Sequence(lambda n: f'test-func-{n}')`
    - `type = 'IsFile'`
    - M2M: `possible_parameters` via post_generation

14. **`TestParameterEntryFactory`** — `experiments.models.TestParameterEntry`
    - `parameter = factory.SubFactory(TestParameterFactory)`
    - `value = 'test-value'`

15. **`AbstractTestFactory`** — `experiments.models.AbstractTest`
    - `ulid = factory.LazyFunction(generate_ulid)`
    - `testfunction = factory.SubFactory(TestFunctionFactory)`
    - M2M: `parameters` via post_generation

16. **`ExperimentFactory`** — `experiments.models.Experiment`
    - `ulid = factory.LazyFunction(generate_ulid)`
    - `name = factory.Sequence(lambda n: f'test-experiment-{n}')`
    - `sha256hash = factory.Sequence(lambda n: hashlib.sha256(f'exp-{n}'.encode()).hexdigest())`
    - `action_file`, `testset_file`, `metadata_file` = placeholder URLs
    - `published_by = factory.SubFactory(GiteaUserFactory)`
    - `published = True`
    - M2M: `environments`, `abstract_tests`, `tags` via post_generation

17. **`ResultFactory`** — `experiments.models.Result`
    - `status = factory.SubFactory(StatusFactory, name='success')`

18. **`ExperimentRunFactory`** — `experiments.models.ExperimentRun`
    - `ulid = factory.LazyFunction(generate_ulid)`
    - `experiment = factory.SubFactory(ExperimentFactory)`
    - `environment = factory.LazyAttribute(lambda o: o.experiment.environments.first() or EnvironmentFactory())`
    - `status = factory.SubFactory(StatusFactory, name='finished')`
    - `result_status = factory.SubFactory(StatusFactory, name='success')`
    - `published_by = factory.SelfAttribute('experiment.published_by')`
    - File fields: `factory.django.FileField(filename='test.log', data=b'test log content')`

### Event Factories

19-25. **`CommandEventFactory`**, **`TestEventFactory`**, **`ErrorEventFactory`**, **`GuiFindEventFactory`**, **`GuiClickEventFactory`**, **`GuiKeypressEventFactory`**, **`GuiIdleEventFactory`**
    - All share: `ulid = LazyFunction(generate_ulid)`, `status = SubFactory(StatusFactory)`, `timestamp = LazyFunction(timezone.now)`
    - `run = factory.SubFactory(ExperimentRunFactory)`
    - Type-specific fields with sensible defaults

### Request Factory

26. **`RequestFactory`** — `experiments.models.Request`
    - `ulid = factory.LazyFunction(generate_ulid)`
    - `requester = factory.SubFactory(GiteaUserFactory)`
    - GenericFK handled via `factory.LazyAttribute`:
      ```python
      objective = factory.LazyAttribute(
          lambda o: ContentType.objects.get_for_model(Experiment)
      )
      object_id = factory.LazyAttribute(lambda o: ExperimentFactory().ulid)
      ```

## Layer 1: pytest Test Cases

### Root conftest.py (`tests/conftest.py`)

Key fixtures:

```python
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
    exp = ExperimentFactory(published_by=gitea_user, environments=[env], abstract_tests=[abstract_test])
    return exp
```

### API conftest.py (`tests/api/conftest.py`)

```python
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, gitea_user):
    """Client with Knox token auth."""
    from knox.models import AuthToken
    _, token = AuthToken.objects.create(gitea_user.user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return api_client

@pytest.fixture(autouse=True)
def mock_external_services(settings):
    """Mock Gitea URL converters and MinIO presigned URLs."""
    with patch('helperfunctions.gitea.convert_gitea_internal_api_url_to_viewable_url', side_effect=lambda x: x), \
         patch('helperfunctions.gitea.convert_gitea_internal_api_url_to_external', side_effect=lambda x: x), \
         patch('helperfunctions.minio.get_presigned_url', return_value='http://mock-minio/file'):
        yield

@pytest.fixture
def eager_celery(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
```

### Test Files

**`test_experiment_endpoints.py`**
| Test | Description |
|------|-------------|
| `test_list_returns_only_published` | Create published + unpublished, verify filter |
| `test_list_pagination` | Verify `limit` and `offset` params |
| `test_list_search_by_name` | `?search=<name>` |
| `test_list_filter_by_tag` | `?tags_mc=<tag>` |
| `test_list_filter_by_min_runcount` | With runs at various result statuses |
| `test_list_includes_run_counts` | Verify `successful_run_count` annotation |
| `test_detail_returns_nested_data` | Environments, abstract_tests, tags serialized |
| `test_detail_404_for_unpublished` | |
| `test_filter_options_returns_tags_and_counts` | |

**`test_run_endpoints.py`**
| Test | Description |
|------|-------------|
| `test_list_all_runs` | |
| `test_list_filter_by_ulid` | |
| `test_list_pagination` | |
| `test_detail_includes_events` | All 7 event types serialized |
| `test_detail_includes_log_urls` | Mocked presigned URLs |
| `test_delete_run` | DELETE removes run and cascades events |
| `test_delete_nonexistent_returns_404` | |
| `test_check_existing_run` | |
| `test_check_nonexistent_run` | |

**`test_run_publish.py`** (most complex)
| Test | Description |
|------|-------------|
| `test_publish_with_command_events` | Full multipart POST with JSON metadata + files |
| `test_publish_with_test_events` | Include test events with results |
| `test_publish_with_all_event_types` | All 7 event types in one request |
| `test_publish_with_log_files` | Verify FileField uploads saved |
| `test_duplicate_run_ulid_rejected` | 400 |
| `test_nonexistent_experiment_rejected` | 400 |
| `test_nonexistent_environment_rejected` | 400 |
| `test_duplicate_event_ulid_rejected` | 400 |
| `test_requires_authentication` | 401 without token |

**`test_environment_endpoints.py`**
| Test | Description |
|------|-------------|
| `test_list_requires_authentication` | 401/403 without token |
| `test_list_returns_only_published` | |
| `test_download_by_name` | |
| `test_filter_options` | |

**`test_testfunction_endpoints.py`**
| Test | Description |
|------|-------------|
| `test_list_returns_published_sets` | |
| `test_list_includes_nested_functions` | TestFunctions with parameters |
| `test_download_by_name` | |

**`test_request_endpoints.py`**
| Test | Description |
|------|-------------|
| `test_list_all_requests` | |
| `test_detail_includes_generic_object` | Polymorphic serialization |
| `test_filter_options_returns_status_and_category` | |

**`test_stats.py`**
| Test | Description |
|------|-------------|
| `test_returns_all_counts` | Verify all count fields present |
| `test_counts_match_database` | Create known data, verify counts |

**`test_submit.py`** (dev mode mock submissions)
| Test | Description |
|------|-------------|
| `test_submit_experiment_returns_fake_pr` | Multipart with playbook + metadata files |
| `test_submit_testfunction_returns_fake_pr` | |
| `test_submit_environment_returns_fake_pr` | |
| `test_submit_requires_authentication` | 401 |
| `test_submit_missing_file_returns_400` | |

**`test_webhook.py`**
| Test | Description |
|------|-------------|
| `test_webhook_accepts_valid_payload` | Returns 200 |
| `test_webhook_empty_payload_returns_400` | |
| `test_webhook_triggers_celery_task` | Verify `.delay()` called |
| `test_webhook_pr_opened_creates_request` | With `eager_celery`, verify Request in DB |
| `test_webhook_pr_merged_publishes` | Full open→merge cycle |

**`test_hash_endpoints.py`**
| Test | Description |
|------|-------------|
| `test_experiment_hash_to_metadata` | |
| `test_environment_hash_to_metadata` | |
| `test_testfunction_hash_to_metadata` | |
| `test_hash_not_found_returns_404` | |

**`test_auth.py`**
| Test | Description |
|------|-------------|
| `test_dev_login_creates_user_and_token` | |
| `test_dev_login_existing_user` | |
| `test_csrf_endpoint_sets_cookie` | |
| `test_protected_endpoint_without_token` | 401 |

**`test_experiment_check.py`** (will catch the `publish_date` bug)
| Test | Description |
|------|-------------|
| `test_check_published_by_hash` | Returns published=True |
| `test_check_unpublished_with_request` | Returns published=False + request_ulid |
| `test_check_nonexistent_hash` | published=None |
| `test_check_missing_param_returns_400` | |
| `test_check_multiple_hashes` | |

## Layer 2: E2E Management Command

File: `experiments/management/commands/test_e2e_gitea.py`

### Command Arguments

```
--skip-cleanup    Don't reset repo after tests (for debugging)
--test-repo       Gitea repo name (default: 'adareTEST')
--repo-owner      Gitea repo owner (default: from settings)
--verbose         Show detailed progress
```

### Orchestration Flow

```
Phase 0: Setup
  ├── Save original GITEA_EXPERIMENTS_REPO setting
  ├── Swap to test repo name
  ├── Set CELERY_TASK_ALWAYS_EAGER = True
  └── Reset state:
      ├── DB: flush → loaddata status → create dev user
      ├── Gitea: close_all_prs → delete_all_branches → clear_branch('main')
      └── Files: clean MEDIA_ROOT/logfiles/

Phase 1: TestFunction Flow
  ├── Upload sample testfunction files to Gitea branch
  ├── Create PR: "[testfunction create] standard"
  ├── Fire webhook (PR opened) → verify Request created in DB
  ├── Merge PR via Gitea API
  ├── Fire webhook (PR merged) → verify TestfunctionSet.published=True
  └── ✓ Assert: TestfunctionSet exists, has TestFunctions

Phase 2: Environment Flow
  ├── Upload sample environment YAML to Gitea branch
  ├── Create PR: "[environment create] testenv"
  ├── Fire webhook (PR opened) → verify Request created
  ├── Merge PR
  ├── Fire webhook (PR merged) → verify Environment.published=True
  └── ✓ Assert: Environment exists with OsInfo

Phase 3: Experiment Flow
  ├── Upload sample playbook + metadata to Gitea branch
  ├── Create PR: "[experiment create] test-experiment"
  ├── Fire webhook (PR opened) → verify Request created
  ├── Merge PR
  ├── Fire webhook (PR merged) → verify Experiment.published=True
  └── ✓ Assert: Experiment linked to Environment and AbstractTests

Phase 4: Run Publish Flow
  ├── POST /api/run/publish/ with:
  │   ├── experiment_ulid, environment_ulid
  │   ├── Status IDs for running → finished, success
  │   ├── Events: 2 command events, 1 test event, 1 error event
  │   └── Log files (SimpleUploadedFile)
  ├── ✓ Assert: ExperimentRun exists with correct status
  ├── ✓ Assert: 4 events created (command, test, error)
  ├── GET /api/run/ → verify run appears in list
  ├── GET /api/experiment/ → verify run counts updated
  └── DELETE /api/run/delete/ → verify cleanup

Phase 5: Verification Summary
  ├── GET /api/stats/ → verify all counts match expectations
  ├── Print pass/fail summary table
  └── Exit code: 0 if all passed, 1 if any failed

Phase 6: Cleanup (unless --skip-cleanup)
  ├── Reset Gitea repo (same as Phase 0)
  ├── Restore original GITEA_EXPERIMENTS_REPO
  └── Print total runtime
```

### Gitea Cleanup Helper

File: `tests/e2e/gitea_cleanup.py`

Refactored from `tests/gitea_tests/pr.py` to accept configuration instead of module-level globals:

```python
class GiteaTestHelper:
    """Manages Gitea repo state for E2E tests."""

    def __init__(self, api_url, api_user, api_password, owner, repo):
        # Initialize giteaapi client from settings
        ...

    def full_reset(self):
        """Close PRs, delete branches, clear files."""
        self.close_all_prs()
        self.delete_all_branches_except_main()
        self.clear_branch('main')

    def create_pr_testfunction(self, name, files_dir): ...
    def create_pr_environment(self, name, file_path): ...
    def create_pr_experiment(self, name, files_dir): ...
    def merge_pr(self, pr_id): ...
    def fire_webhook(self, pr_data, action): ...
```

This reuses the same Gitea API patterns from `pr.py` but parameterized via Django settings.

## Test Fixture Files

Minimal but valid sample files for both layers:

- **`sample_playbook.yml`**: Valid Ansible playbook structure (minimal)
- **`sample_metadata.yml`**: Valid experiment metadata YAML
- **`sample_testfunction.py`**: Python file with test function class
- **`sample_requirements.txt`**: `requests>=2.28`
- **`sample_environment.yml`**: Valid environment YAML config
- **`sample_logfile.txt`**: Simple text log content
- **`webhook_payloads/*.json`**: Realistic Gitea webhook payloads (PR open/merge for each type)

## Makefile Targets

Add to `backend_django/Makefile`:

```makefile
test: ## Run API integration tests (Layer 1)
	docker compose exec web python -m pytest tests/api/ -v --tb=short

test-quick: ## Run fast tests only (skip slow-marked)
	docker compose exec web python -m pytest tests/api/ -v -m "not slow"

test-e2e: ## Run E2E Gitea flow tests (Layer 2)
	docker compose exec web python manage.py test_e2e_gitea

test-e2e-debug: ## Run E2E tests without cleanup
	docker compose exec web python manage.py test_e2e_gitea --skip-cleanup --verbose

test-all: ## Run both test layers
	docker compose exec web python -m pytest tests/api/ -v --tb=short && \
	docker compose exec web python manage.py test_e2e_gitea

test-cov: ## Run tests with coverage report
	docker compose exec web python -m pytest tests/api/ -v --cov=experiments --cov=users --cov=giteaeventmanager --cov-report=term-missing
```

## Known Bug to Fix

`experiments/views.py:253` — `ExperimentCheckView` references `experiment.publish_date` which doesn't exist on the `Experiment` model. Should be `experiment.published_at`. Same issue on lines 288. The test `test_check_published_by_hash` will catch this.

## Verification

After implementation, verify the system works:

1. **Install test deps:** `docker compose exec web uv pip install pytest pytest-django factory-boy pytest-cov`
2. **Run Layer 1:** `make test` → all tests should pass (some will expose bugs like `publish_date`)
3. **Run Layer 2:** `make test-e2e` → full Gitea flow completes, repo is cleaned up
4. **Check coverage:** `make test-cov` → review untested code paths
5. **Verify reset:** After `make test-e2e`, check that `adareTEST` repo is clean (no stale branches/PRs)

.PHONY: up down migrate shell logs seed seed-paper unseed-paper react deploy deploy-react deploy-all db-backup deploy-check deploy-migrate deploy-dry-run db-reset-and-init remote-status remote-logs remote-celery-logs deploy-setup help test test-api test-ingest test-quick test-e2e test-e2e-debug test-e2e-interactive-react test-all test-cov react-test

COMPOSE = podman compose -f backend_django/docker-compose.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start all services (podman compose up --build)
	$(COMPOSE) up --build

down: ## Stop all services
	$(COMPOSE) down

migrate: ## Run Django migrations
	$(COMPOSE) exec web python manage.py migrate

shell: ## Open Django shell
	$(COMPOSE) exec web python manage.py shell

logs: ## Follow web container logs
	$(COMPOSE) logs -f web

seed: ## Load sample dev data
	$(COMPOSE) exec web python manage.py seed_dev_data

seed-paper:   ## Seed paper-evaluation demo data (local dev only)
	$(COMPOSE) exec web python manage.py seed_paper_data

unseed-paper: ## Remove paper-evaluation demo data
	$(COMPOSE) exec web python manage.py seed_paper_data --purge

react: ## Start React dev server
	cd frontend_react && npm run dev

deploy: ## Deploy backend to production
	backend_django/deploy/deploy-backend.sh

deploy-react: ## Deploy React frontend to production
	backend_django/deploy/deploy-react.sh

deploy-all: ## Deploy backend + React frontend to production
	backend_django/deploy/deploy-backend.sh && backend_django/deploy/deploy-react.sh

db-backup: ## Backup production database
	backend_django/deploy/db-backup.sh

remote-status: ## Show remote Docker service status
	ssh adare "cd ~/webapp && podman compose ps"

remote-logs: ## Follow remote backend logs
	ssh adare "cd ~/webapp && podman compose logs -f backend"

deploy-check: ## Run post-deploy health checks
	backend_django/deploy/deploy-check.sh

deploy-migrate: ## Run migrations only (no code upload)
	backend_django/deploy/deploy-backend.sh --migrate-only

deploy-dry-run: ## Preview what a deploy would do
	backend_django/deploy/deploy-backend.sh --dry-run

db-reset-and-init: ## Full DB nuke + reinitialize
	backend_django/deploy/db-reset-and-init.sh

remote-celery-logs: ## Follow Celery worker logs
	ssh adare "cd ~/webapp && podman compose logs -f celery_worker"

deploy-setup: ## Bootstrap local prod files from remote backup (run once)
	backend_django/deploy/deploy-setup.sh

# `tests/`, not `tests/api/`: the service-level suites live directly under
# tests/ (test_ingest_service.py, test_serializers.py, test_models.py, ...) and
# were outside every advertised target, so 91 ingest tests never ran in CI.
test: ## Run all pytest suites — service + API integration (Layer 1)
	$(COMPOSE) exec web python -m pytest tests/ -v --tb=short

test-api: ## Run only the API integration tests (tests/api/)
	$(COMPOSE) exec web python -m pytest tests/api/ -v --tb=short

test-ingest: ## Run only the ingest-service suite (recipe / BYO ISO / provision)
	$(COMPOSE) exec web python -m pytest tests/test_ingest_service.py -v --tb=short

test-quick: ## Run fast tests only (skip slow-marked)
	$(COMPOSE) exec web python -m pytest tests/ -v -m "not slow"

test-e2e: ## Run E2E Gitea flow tests (Layer 2)
	$(COMPOSE) exec web python manage.py test_e2e_gitea

test-e2e-debug: ## Run E2E tests without cleanup
	$(COMPOSE) exec web python manage.py test_e2e_gitea --skip-cleanup --verbose

react-test: ## Run React frontend tests
	cd frontend_react && npm test

test-e2e-interactive-react: ## Run E2E tests with React frontend for GUI inspection
	@echo "Starting containers..."
	@$(COMPOSE) up --build -d
	@echo "Starting React dev server..."
	@cd frontend_react && npm run dev > /dev/null 2>&1 & echo $$! > /tmp/adare-react-dev.pid
	@sleep 3
	@echo "React dev server running at http://localhost:5173"
	@echo ""
	@$(COMPOSE) exec web python manage.py test_e2e_gitea --interactive --verbose; \
		EXIT_CODE=$$?; \
		if [ -f /tmp/adare-react-dev.pid ]; then \
			kill $$(cat /tmp/adare-react-dev.pid) 2>/dev/null; \
			rm -f /tmp/adare-react-dev.pid; \
			echo "React dev server stopped."; \
		fi; \
		echo "Stopping containers..."; \
		$(COMPOSE) down; \
		exit $$EXIT_CODE

test-all: ## Run both test layers
	$(COMPOSE) exec web python -m pytest tests/ -v --tb=short && \
	$(COMPOSE) exec web python manage.py test_e2e_gitea

test-cov: ## Run tests with coverage report
	$(COMPOSE) exec web python -m pytest tests/ -v --cov=experiments --cov=users --cov=giteaeventmanager --cov-report=term-missing

.DEFAULT_GOAL := help

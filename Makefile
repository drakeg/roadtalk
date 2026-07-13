SHELL := /bin/sh
COMPOSE ?= docker compose
ENV_FILE ?= .env
BACKEND_PYTHON ?= python3.12
BACKEND_VENV ?= backend/.venv
BACKEND_BIN := $(BACKEND_VENV)/bin

.DEFAULT_GOAL := help

.PHONY: help prerequisites setup config up up-redis wait ps logs down reset database-shell redis-cli verify-database backend-install backend-run backend-migrate backend-migration-check backend-migration-downgrade backend-format-check backend-lint backend-typecheck backend-test mobile-install mobile-start mobile-ios mobile-android mobile-doctor mobile-typecheck mobile-test terraform-validate

help: ## Show local development commands.
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

prerequisites: ## Verify required local tools.
	@sh scripts/check-prerequisites.sh

setup: prerequisites ## Create .env from the safe local example when absent and validate Compose.
	@if [ ! -f "$(ENV_FILE)" ]; then cp .env.example "$(ENV_FILE)"; echo "Created $(ENV_FILE) from .env.example"; fi
	@$(MAKE) config

config: ## Validate the resolved Docker Compose configuration.
	@test -f "$(ENV_FILE)" || { echo "Missing $(ENV_FILE). Run 'make setup'."; exit 1; }
	@$(COMPOSE) --env-file "$(ENV_FILE)" config --quiet

up: setup ## Start PostgreSQL/PostGIS and wait until healthy.
	@$(COMPOSE) --env-file "$(ENV_FILE)" up -d --wait database

up-redis: setup ## Start PostgreSQL/PostGIS plus optional Redis and wait until healthy.
	@$(COMPOSE) --env-file "$(ENV_FILE)" --profile redis up -d --wait

wait: ## Wait for the local database to become healthy.
	@sh scripts/wait-for-local-services.sh

ps: ## Show local service status.
	@$(COMPOSE) --env-file "$(ENV_FILE)" ps

logs: ## Follow local service logs.
	@$(COMPOSE) --env-file "$(ENV_FILE)" logs --follow --tail=200

down: ## Stop local services without deleting data.
	@$(COMPOSE) --env-file "$(ENV_FILE)" --profile redis down

reset: ## Delete local containers and data; requires CONFIRM_RESET=yes.
	@test "$(CONFIRM_RESET)" = "yes" || { echo "Refusing destructive reset. Re-run with CONFIRM_RESET=yes."; exit 1; }
	@$(COMPOSE) --env-file "$(ENV_FILE)" --profile redis down --volumes --remove-orphans

database-shell: ## Open psql inside the local database container.
	@$(COMPOSE) --env-file "$(ENV_FILE)" exec database psql -U "$${POSTGRES_USER:-roadtalk}" -d "$${POSTGRES_DB:-roadtalk}"

redis-cli: ## Open redis-cli when the optional Redis profile is running.
	@$(COMPOSE) --env-file "$(ENV_FILE)" --profile redis exec redis redis-cli

verify-database: ## Verify PostgreSQL and PostGIS are available.
	@$(COMPOSE) --env-file "$(ENV_FILE)" exec -T database psql -U "$${POSTGRES_USER:-roadtalk}" -d "$${POSTGRES_DB:-roadtalk}" -v ON_ERROR_STOP=1 -c "SELECT current_database(), PostGIS_Full_Version();"

backend-install: ## Create the backend virtual environment and install development dependencies.
	@$(BACKEND_PYTHON) -m venv "$(BACKEND_VENV)"
	@$(BACKEND_BIN)/pip install -e 'backend[dev]'

backend-run: ## Run the local FastAPI development server.
	@test -f "$(ENV_FILE)" || { echo "Missing $(ENV_FILE). Run 'make setup'."; exit 1; }
	@set -a; . ./$(ENV_FILE); set +a; cd backend && ../$(BACKEND_BIN)/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

backend-migrate: ## Upgrade the configured database to the latest migration.
	@test -f "$(ENV_FILE)" || { echo "Missing $(ENV_FILE). Run 'make setup'."; exit 1; }
	@set -a; . ./$(ENV_FILE); set +a; cd backend && ../$(BACKEND_BIN)/alembic upgrade head

backend-migration-check: ## Fail when metadata differs from the migrated database.
	@test -f "$(ENV_FILE)" || { echo "Missing $(ENV_FILE). Run 'make setup'."; exit 1; }
	@set -a; . ./$(ENV_FILE); set +a; cd backend && ../$(BACKEND_BIN)/alembic check

backend-migration-downgrade: ## Downgrade one revision (local recovery/testing only).
	@test -f "$(ENV_FILE)" || { echo "Missing $(ENV_FILE). Run 'make setup'."; exit 1; }
	@set -a; . ./$(ENV_FILE); set +a; cd backend && ../$(BACKEND_BIN)/alembic downgrade -1

backend-format-check: ## Check backend formatting.
	@$(BACKEND_BIN)/ruff format --check backend

backend-lint: ## Lint the backend.
	@$(BACKEND_BIN)/ruff check backend

backend-typecheck: ## Type-check the backend.
	@cd backend && ../$(BACKEND_BIN)/mypy app tests

backend-test: ## Run backend tests with branch coverage.
	@cd backend && ../$(BACKEND_BIN)/pytest --cov=app --cov-branch --cov-report=term-missing

mobile-install: ## Install the locked mobile dependencies.
	@cd mobile && npm ci

mobile-start: ## Start Metro for the Expo development client.
	@cd mobile && npm start

mobile-ios: ## Generate/run the local iOS development build.
	@cd mobile && npm run ios

mobile-android: ## Generate/run the local Android development build.
	@cd mobile && npm run android

mobile-doctor: ## Validate Expo dependency and project configuration.
	@cd mobile && npm run doctor

mobile-typecheck: ## Type-check the mobile application.
	@cd mobile && npm run typecheck

mobile-test: ## Run mobile foundation tests.
	@cd mobile && npm test

terraform-validate: ## Validate disabled Terraform plans and cost/security guardrails.
	@sh scripts/ci/validate-terraform.sh

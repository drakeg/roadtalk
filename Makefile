SHELL := /bin/sh
COMPOSE ?= docker compose
ENV_FILE ?= .env

.DEFAULT_GOAL := help

.PHONY: help prerequisites setup config up up-redis wait ps logs down reset database-shell redis-cli verify-database

help: ## Show local development commands.
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

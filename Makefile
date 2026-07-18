COMPOSE=docker compose

.PHONY: help up down build logs shell status reset seed fresh test clean migrate-upgrade migrate-downgrade migrate-history migrate-current migrate-stamp migrate-stamp-head

help:
	@echo "Available commands:"
	@echo "  -------------Docker-------------"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make build     - Rebuild project image"
	@echo "  make logs      - View backend logs"
	@echo "  make shell     - Open backend shell"
	@echo "  ------------Database------------"
	@echo "  make status    - View database status"
	@echo "  make reset     - Reset database"
	@echo "  make seed      - Seed database"
	@echo "  make fresh     - Reset & seed database"
	@echo "  ----------Migrations------------"
	@echo "  make migrate-upgrade                - Run all pending migrations"
	@echo "  make migrate-downgrade REVISION=-1  - Rollback migrations"
	@echo "  make migrate-history                - Show migration history"
	@echo "  make migrate-current                - Show current revision"
	@echo "  make migrate-stamp REVISION=...     - Mark DB as current without running"
	@echo "  make migrate-stamp-head             - Stamp DB to latest revision (fix broken chains)"
	@echo "  ------------Testing-------------"
	@echo "  make test      - Run test suite"
	@echo "  ------------Cleaning------------"
	@echo "  make clean     - Remove Docker resources"

up:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml up -d

down:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml down

build:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml build

logs:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml logs -f backend

shell:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend sh

status:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend python -m manage status

reset:
	@printf "This operation will reset the database. Continue? [y/N] "
	@read ans; \
	if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend python -m manage reset

seed:
	@echo "=== Seeding database (with auto-fetch/generate) ==="
	@$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend \
		python -m manage seed all --ensure-fixtures --profile default

fresh:
	@printf "This operation will reset the database. Continue? [y/N] "
	@read ans; \
	if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend python -m manage reset --seed all

test:
	@echo "Starting test services (PostgreSQL, Redis, and backend)..."
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml --profile test up --build -d
	@echo "Waiting for backend test container to complete..."
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml logs -f backend
	@echo "Test completed, cleaning up..."
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml down -v --remove-orphans

clean:
	@printf "This operation will wipe the database and redis containers. Continue? [y/N] "
	@read ans; \
	if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml --profile frontend down -v --remove-orphans
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml rm -f
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml down -v --remove-orphans
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml rm -f

# ---------- Migrations ----------

MANAGE = python -m manage migrate

migrate-upgrade:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend $(MANAGE) run

migrate-downgrade:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend $(MANAGE) downgrade $(REVISION)

migrate-history:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend $(MANAGE) history

migrate-current:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend $(MANAGE) current

migrate-stamp:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend $(MANAGE) stamp $(REVISION)

migrate-stamp-head:
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend $(MANAGE) stamp head

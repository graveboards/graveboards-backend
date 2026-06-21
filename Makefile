COMPOSE=docker compose

.PHONY: help up down build logs shell status reset seed fresh test clean

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
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml exec backend python -m manage seed all

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
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml down -v --remove-orphans
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.yml rm -f
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml down -v --remove-orphans
	$(COMPOSE) -f ../graveboards-deploy/docker-compose.test.yml rm -f

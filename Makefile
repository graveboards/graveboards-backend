COMPOSE=docker compose
MANAGE=$(COMPOSE) run -q --rm graveboards-manage python -m manage
ENV := $(shell echo $(ENV) | tr '[:upper:]' '[:lower:]')

ifeq ($(ENV),prod)
$(error This Makefile may not be used in production)
endif

.PHONY: help up down build logs shell wipe status reset seed fresh

help:
	@echo "Available commands:"
	@echo "  -------------Docker-------------"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make build     - Rebuild project image"
	@echo "  make logs      - View backend logs"
	@echo "  make shell     - Open backend shell"
	@echo "  make wipe      - Destroy database volumes"
	@echo "  ------------Database------------"
	@echo "  make status    - View database status"
	@echo "  make reset     - Reset database"
	@echo "  make seed      - Seed database"
	@echo "  make fresh     - Reset & seed database"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f graveboards-backend

shell:
	$(COMPOSE) exec graveboards-backend sh

wipe:
	@printf "This operation will irreversibly destroy database and redis volumes. Continue? [y/N] "
	@read ans; \
	if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	$(COMPOSE) down -v

status:
	$(MANAGE) status

reset:
	@printf "This operation will reset the database. Continue? [y/N] "
	@read ans; \
	if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	$(MANAGE) reset

seed:
	$(MANAGE) seed all

fresh:
	@printf "This operation will reset the database. Continue? [y/N] "
	@read ans; \
	if [ "$$ans" != "y" ] && [ "$$ans" != "Y" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	$(MANAGE) reset --seed all
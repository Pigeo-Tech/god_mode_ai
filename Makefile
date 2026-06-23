# GOD MODE AI — common developer tasks
COMPOSE_DEV  := docker compose -f docker/docker-compose.yml
COMPOSE_PROD := docker compose -f docker/docker-compose.prod.yml --env-file .env

.PHONY: help test build up down prod-up prod-down logs shell

help:
	@echo "test       run the backend test suite (offline harness)"
	@echo "build      build the backend image"
	@echo "up/down    start/stop the dev stack (api+postgres+redis+qdrant)"
	@echo "prod-up    start the production-like stack (+nginx)"
	@echo "logs       tail dev stack logs"

test:
	python3 scripts/run_tests.py

build:
	docker build -f docker/Dockerfile -t god-mode-ai:dev .

up:
	$(COMPOSE_DEV) up --build

down:
	$(COMPOSE_DEV) down -v

prod-up:
	$(COMPOSE_PROD) up -d --build

prod-down:
	$(COMPOSE_PROD) down

logs:
	$(COMPOSE_DEV) logs -f api

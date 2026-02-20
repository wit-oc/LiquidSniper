PYTHON ?= python3

.PHONY: venv test lint run-web run-ingestor paper-daemon-up paper-daemon-down paper-daemon-logs paper-scorecard-once

venv:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip

test:
	$(PYTHON) -m pytest -q

lint:
	@echo "No linter configured yet"

run-web:
	$(PYTHON) -m streamlit run liquidsniper/web/app.py

run-ingestor:
	$(PYTHON) -m liquidsniper.ingestor.main

paper-daemon-up:
	docker compose -f docker-compose.paper.yml --env-file .env.paper up -d paper-runner

paper-daemon-down:
	docker compose -f docker-compose.paper.yml --env-file .env.paper down

paper-daemon-logs:
	docker compose -f docker-compose.paper.yml --env-file .env.paper logs -f --tail=200 paper-runner

paper-scorecard-once:
	docker compose -f docker-compose.paper.yml --env-file .env.paper run --rm scorecard-worker

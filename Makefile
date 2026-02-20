PYTHON ?= python3

.PHONY: venv test lint run-web run-ingestor paper-daemon-up paper-daemon-down paper-daemon-logs paper-scorecard-once paper-backup-state paper-reset-state

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

paper-backup-state:
	@mkdir -p backups
	@TS=$$(date -u +%Y%m%dT%H%M%SZ); \
	docker run --rm -v liquidsniper_liquidsniper_data:/data -v "$$(pwd)/backups":/backup alpine sh -lc "tar czf /backup/paper_mvp_pre_reset_$${TS}.tgz -C /data artifacts/paper_mvp logs || true"; \
	echo "backup written: backups/paper_mvp_pre_reset_$${TS}.tgz"

paper-reset-state:
	docker compose -f docker-compose.paper.yml --env-file .env.paper down
	docker compose -f docker-compose.paper.yml --env-file .env.paper run --rm scorecard-worker sh -lc "rm -rf /var/lib/liquidsniper/artifacts/paper_mvp/runs/* /var/lib/liquidsniper/artifacts/paper_mvp/daily/* /var/lib/liquidsniper/artifacts/paper_mvp/weekly/* /var/lib/liquidsniper/artifacts/paper_mvp/state/* /var/lib/liquidsniper/logs/*; mkdir -p /var/lib/liquidsniper/artifacts/paper_mvp/runs /var/lib/liquidsniper/artifacts/paper_mvp/daily /var/lib/liquidsniper/artifacts/paper_mvp/weekly /var/lib/liquidsniper/artifacts/paper_mvp/state /var/lib/liquidsniper/logs; echo reset-done"

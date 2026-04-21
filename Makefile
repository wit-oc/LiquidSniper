PYTHON ?= python3

.PHONY: venv test lint run-web run-ingestor

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

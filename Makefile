PYTHON ?= python3

.PHONY: test lint run-web run-ingestor

test:
	$(PYTHON) -m pytest

lint:
	@echo "No linter configured yet"

run-web:
	$(PYTHON) -m streamlit run liquidsniper/web/app.py

run-ingestor:
	$(PYTHON) -m liquidsniper.ingestor.main

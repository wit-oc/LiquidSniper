# Development Setup

## 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install project dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

## 3) Verify scaffold

```bash
python -c "import liquidsniper"
python -m pytest
```

## 4) Convenience targets

```bash
make test
make run-ingestor
make run-web
```

## Notes

- No Telegram login or network calls are required for scaffold validation.
- If your Python is externally managed (PEP 668), always install in `.venv`.

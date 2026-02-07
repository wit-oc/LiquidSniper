# Local Dev Setup

Use this setup before running tests/reviewing branches.

## 1) Create virtual env

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 2) Install dependencies

Choose whichever is present in the branch:

### If `pyproject.toml` is present

```bash
pip install -e ".[dev]"
```

### If requirements files are present

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 3) Validate environment

```bash
python -c "import liquidsniper; print('ok')"
pytest -q
```

## 4) Optional helpers

If `Makefile` exists:

```bash
make test
```

## Notes

- Keep `.venv/` local; it is gitignored.
- If tests fail due to missing deps, reinstall after pulling latest branch changes.

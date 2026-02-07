# Codex CLI on Mac mini — Setup & PR Runbook

Goal: enable a local codex-driven workflow where implementation happens on feature branches, with tests + security checks in each PR, and Redact as approver.

## 0) Environment check (current mini)

Verified on this host:
- Python: `3.9.6`
- Git: installed
- GitHub CLI (`gh`): installed
- Docker + Compose: installed
- Node + npm: installed
- Codex CLI: **not installed yet**

## 1) Install Codex CLI

Use one of:

### Option A — npm (recommended)

```bash
npm i -g @openai/codex
codex --version
```

### Option B — Homebrew cask

```bash
brew install --cask codex
codex --version
```

## 2) Authenticate Codex CLI

Run:

```bash
codex login
```

Confirm:

```bash
codex whoami
```

If your Codex setup supports model selection, set/check GPT-5.3 Codex as default for coding runs.

## 3) Repository prerequisites

```bash
cd /Users/wit/.openclaw/workspace/LiquidSniper
git pull origin main
```

Create and use local venv for test/validation:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install project deps (branch-dependent):

```bash
# If pyproject present
pip install -e ".[dev]"

# Or requirements files
pip install -r requirements.txt -r requirements-dev.txt
```

## 4) Branch workflow

For each task:

```bash
git checkout main
git pull origin main
git checkout -b task-XX-short-name
```

Run Codex with the task prompt provided by Wit.

Commit in logical chunks:

```bash
git add -A
git commit -m "task-XX: <what changed>"
git push -u origin task-XX-short-name
```

Open PR to `main`.

## 5) Required validation before opening PR

### Functional tests

```bash
source .venv/bin/activate
pytest -q
python -c "import liquidsniper; print('ok')"
```

### Security checks (minimum)

Install once in venv:

```bash
pip install pip-audit bandit
```

Run:

```bash
pip-audit
bandit -q -r liquidsniper
```

Optional secret scan (recommended if available):
- `gitleaks detect --no-git`

## 6) PR checklist (must include)

In PR description include:
- Spec/task references satisfied
- Test evidence (`pytest` summary)
- Security evidence (`pip-audit`, `bandit` outputs)
- Any schema changes + migration notes

Also ensure `docs/PRE_MERGE_CHECKLIST.md` is fully satisfied.

## 7) Suggested GitHub protections

For `main` branch:
- Require pull request before merge
- Require at least 1 approval (Redact)
- Require status checks to pass (once CI is added)
- Block force pushes to main

## 8) Operational model (hybrid)

- Codex CLI: implementation engine (fast code/test generation)
- Wit agent: architecture guardrails, review, integration, and prompt design
- Redact: final approver/merge gate

# Contributing to MatchDay AI

Thanks for your interest in improving MatchDay AI! This guide covers local
setup and the checks your change is expected to pass.

## Prerequisites

- Python **3.11+** (the project is developed and tested on 3.14)
- A Gemini API key (optional for most tests — the AI layer is mocked in the
  test suite)

## Local setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Install runtime + development dependencies
pip install -r requirements-dev.txt

# 3. Configure environment variables
cp .env.example .env                # then set GEMINI_API_KEY

# 4. Run the app
uvicorn app.main:app --reload
```

The fan assistant is served at `http://localhost:8000/` and the staff
dashboard at `http://localhost:8000/dashboard`.

## Running the checks

Every change should pass all of the following before opening a PR:

```bash
# Lint
ruff check app tests

# Tests + coverage (unit + integration; e2e are deselected by default)
pytest --cov=app --cov-report=term-missing

# Type check
mypy app

# Docstring coverage
interrogate app
```

### End-to-end tests

The Playwright-driven e2e tests are marked `e2e` and excluded from the default
run. To run them locally:

```bash
playwright install chromium
pytest -m e2e
```

## Pull request expectations

- Keep public API paths, request/response field names, and status codes
  **stable** — coordinate first if a breaking change is genuinely needed.
- Add or update tests for any behavior you change.
- Keep `ruff`, `mypy`, and `interrogate` green; do not lower `fail_under`
  coverage thresholds without discussion.
- Add a note to [`CHANGELOG.md`](CHANGELOG.md) under an *Unreleased* section
  describing your change.
- Write clear, focused commits and a PR description explaining the *why*.

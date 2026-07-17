# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

MatchDay AI — a FastAPI smart-stadium assistant (Hack2Skill "Virtual Prompt Wars" Challenge 4).
Server-rendered Jinja2 pages + vanilla `fetch()` JS, no frontend build step. Gemini is used
only as a natural-language *phrasing layer* over deterministic Python logic.

## Environment

- Python **3.11+** (developed/tested on 3.14). Use the checked-in virtualenv: `source venv/bin/activate`.
- Dev tooling lives in `requirements-dev.txt` (`ruff`, `mypy`, `interrogate`, `pytest-cov`);
  runtime-only deps are in `requirements.txt`.
- `GEMINI_API_KEY` is read from `.env` (copy `.env.example`). Tests mock Gemini, so most run
  without a key.

## Commands

```bash
# Run the dev server
uvicorn app.main:app --reload           # / (fan assistant), /dashboard (staff)

# Tests — e2e is DESELECTED by default (see pytest marker below)
pytest                                   # unit + integration
pytest --cov=app --cov-report=term-missing
pytest tests/test_crowd.py::test_tick_updates_occupancy_within_bounds   # single test
pytest -m e2e                            # Playwright browser tests (needs: playwright install chromium)

# Quality gates (identical to CI in .github/workflows/ci.yml)
ruff check app tests
mypy app                                 # strict mode
interrogate app                          # docstring coverage, enforced at 100%
```

All tool config is centralized in `pyproject.toml` (there is no `pytest.ini`). CI enforces
strict gates: **100% line+branch coverage** (`fail_under`), `mypy --strict`, `interrogate` at
100%, ruff (88-col, `C90` complexity ≤10), and `pip-audit`.

## Architecture

Request flow is a strict layering — **routes → services → (Gemini | venue data)**:

- **`app/routes/*.py`** — thin FastAPI handlers, one per feature. They validate via a Pydantic
  model, call a service, and translate exceptions to HTTP: `NoRouteFoundError` → 404, service
  `RuntimeError` → 502 (via `app/routes/errors.py::ai_service_unavailable`). Route handlers are
  annotated `-> dict[str, object]`; this is a pass-through response model and must not change the
  JSON shape.
- **`app/services/*.py`** — all business logic. Routing (`wayfinding.py`, Dijkstra over the venue
  graph), the in-memory crowd simulator (`crowd.py`), accessibility matching, sustainability
  ranking, transport suggestion. **These are deterministic and fully unit-tested** — the AI only
  phrases already-computed results.
- **`app/services/gemini.py`** — the *only* module that touches the Gemini API or the API key.
  Everything goes through `ask_gemini(prompt)`, which owns the timeout and wraps every failure as
  `RuntimeError`. Callers catch that and fail closed.
- **`app/services/venue_repository.py`** — loads/caches `app/data/venue.json` (`lru_cache`) and
  exposes the graph as an adjacency list. `venue.json` is the single source of truth for gates,
  sections, facilities, and edges.
- **`app/services/i18n.py`** — shared language-code → name table; unknown codes fall back to English.

### Things that will bite you

- **Never change public route paths, request/response field names, or status codes.** This is a
  scored, resubmitted competition project; behavior is frozen. Add tests/docs/config/internal
  cleanup only.
- **Enums are `StrEnum`** (`app/models/requests.py`, `sustainability.py`). They serialize by value.
- **The crowd simulator is a module-level singleton** (`crowd.simulator`) started/stopped by the
  FastAPI `lifespan` in `app/main.py`. `tests/conftest.py` resets its state between tests; pass a
  seeded `random.Random` to `tick(rng=...)` for deterministic crowd tests.
- **e2e tests are marked `e2e` and excluded from the default run** (Playwright's sync API conflicts
  with pytest-asyncio's loop, and they need a browser). Run them explicitly with `-m e2e`.
- **Accessibility is graded.** `tests/e2e/test_accessibility_scan.py` asserts zero axe-core
  violations on both pages; keep headings as one `<h1>` → `<h2>` sections and preserve ARIA/labels.
  See `docs/accessibility-report.md`.

## Reference docs

- `docs/decisions.md` — rationale for key architectural tradeoffs.
- `docs/accessibility-report.md` — WCAG 2.1 AA audit findings.
- `README.md` — full feature/API reference and deployment (Railway) notes.

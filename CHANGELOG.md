# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Continuous integration (GitHub Actions): ruff lint, mypy (strict) type
  checking, interrogate docstring coverage, pytest with coverage, and a
  `pip-audit` dependency-vulnerability scan.
- CodeQL security scanning workflow (push, PR, and weekly schedule).
- `pyproject.toml` centralizing ruff, pytest, coverage, mypy, and interrogate
  configuration.
- `requirements-dev.txt` for development tooling.
- `SECURITY.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), and this changelog.
- `docs/decisions.md` — architecture decision log (rationale for key tradeoffs).
- `docs/accessibility-report.md` — WCAG 2.1 AA audit (axe-core + manual review).
- mccabe cyclomatic-complexity linting (`C90`, `max-complexity = 10`).
- Expanded test suite (43 → 89 tests) reaching 100% line and branch coverage,
  covering service edge/error paths, all route success/422/502 shapes, and
  rate limiting across every AI route.

### Changed
- Modernized the language/need/transport enums to `enum.StrEnum`.
- Added complete type annotations across `app/` (passes `mypy --strict`).
- Wrapped all source to an 88-column line length (Black/PEP8-adjacent).

### Accessibility
- Fixed heading structure on both pages: a single `<h1>` followed by `<h2>`
  section headings (was multiple `<h1>`s).
- Lifted the dark-theme luminance of the occupancy-tinted map labels so they
  clear WCAG AA (4.5:1) as normal text, without dropping their color coding.

## [1.0.0] - 2026-07-11

### Added
- Initial submission for the Hack2Skill Virtual Prompt Wars (Challenge 4).
- Multilingual AI wayfinding: Dijkstra routing over the venue graph with
  Gemini-phrased, step-free-aware directions.
- Live crowd density simulation with AI-generated reroute alerts for staff.
- Accessibility concierge matching needs to facilities and drafting plans.
- Sustainability advisor comparing arrival-mode impact.
- Transport suggestion endpoint based on distance to the venue.
- Fan-facing assistant and staff operations dashboard, with security headers,
  CORS, and per-client rate limiting on AI routes.

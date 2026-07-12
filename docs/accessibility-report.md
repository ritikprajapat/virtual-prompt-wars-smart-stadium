# Accessibility Audit Report

Audit of the two rendered pages — the fan assistant (`/`) and the staff
dashboard (`/dashboard`) — against **WCAG 2.1 Level AA**.

- **Date:** 2026-07-12
- **Method:**
  1. **Automated** — [axe-core](https://github.com/dequelabs/axe-core) run via
     Playwright (Chromium) against both live pages. This is wired into the test
     suite as `tests/e2e/test_accessibility_scan.py` (`pytest -m e2e`) and
     asserts **zero violations** on every run.
  2. **Manual** — template review for alt text, label associations, ARIA on
     custom widgets, heading structure, and keyboard order; plus explicit
     color-contrast measurement of the dark theme (axe cannot compute contrast
     for SVG text).

## Automated results (axe-core)

| Page | Violations | Rules passed | Needs review (incomplete) |
|------|-----------:|-------------:|---------------------------|
| `/` (fan assistant) | **0** | 41 | `color-contrast` (SVG text only) |
| `/dashboard` (staff) | **0** | 41 | `color-contrast` (SVG text only) |

Notable rules passing on both pages: `color-contrast` (all HTML text),
`label`, `button-name`, `link-name`, `aria-*` (roles/attrs/values),
`heading-order`, `page-has-heading-one`, `landmark-one-main`,
`landmark-unique`, `bypass` (skip link), `document-title`, `html-has-lang`,
`th-has-data-cells` / `td-headers-attr` / `scope-attr-valid` (data table),
`aria-progressbar-name`, `svg-img-alt`.

The only `incomplete` (manual-review) result is `color-contrast` on **SVG
`<text>` elements** in the stadium map and trend chart. axe reports these as
incomplete — not failing — because it cannot resolve the effective background
of text painted over SVG shapes/gradients ("background could not be determined
because element contains an image node / is overlapped"). These were checked
manually below.

## Manual findings and fixes

### 1. Heading structure — FIXED

**Finding:** Both pages used multiple `<h1>` elements (each feature/panel title
was an `<h1>`). This is valid HTML5 and not an axe violation, but it produces a
flat heading outline that is poor for screen-reader navigation (WCAG 2.4.6,
1.3.1).

**Fix:**
- `/` — the hero remains the single page `<h1>`; the four tool titles
  (Wayfinding, Accessibility, Getting Here, Sustainability) are now `<h2>`.
- `/dashboard` — added one visually-hidden page `<h1>` ("Staff Operations
  Dashboard") and demoted the four panel titles to `<h2>`.
- Result on both pages: exactly one `<h1>` followed by `<h2>` section headings
  (`H1 → H2 H2 H2 H2`). Styling was unchanged (the titles are styled by class,
  not tag).

### 2. SVG label color contrast (dark theme) — FIXED

**Finding:** Map/chart labels are painted in the occupancy tint. Measured
against the map background `#121a2c`:

| Element | Color | Ratio | Verdict (11px normal text needs 4.5:1) |
|---------|-------|------:|----------------------------------------|
| Gate letters (`A`, `B`, …) | `--mist` `#93a0bc` | **6.61:1** | Pass |
| Gate load % — low/green | `--pitch` `#2f8f5b` | 4.3:1 | **Below AA** for normal text (passes 3:1 large/graphical) |
| Gate load % — moderate/gold | `--gold` `#d9a94e` | ~7.8:1 | Pass |
| Gate load % — busy/coral | `--coral` `#e2694f` | ~5.3:1 | Pass |

**Fix:** Added `filter: brightness(1.3)` to `.node-pct` — this lifts the
luminance of the occupancy-tinted label (green effective ratio ≈ 6:1) while
preserving its color coding, and the redundant marker circle continues to carry
occupancy state (so information is never conveyed by the label color alone —
WCAG 1.4.1). No layout or palette change.

### 3. Items verified correct (no change needed)

- **Alt text / non-text content:** decorative SVGs and glyphs carry
  `aria-hidden="true"`; informative SVGs (`#mini-map`, `#stadium-map`) use
  `role="img"` with descriptive `aria-label`s, and the stadium map's label
  points users to the data table for exact figures.
- **Form labels:** every `<input>`, `<select>`, and `<textarea>` has an
  associated `<label for>`; radio groups are wrapped in `<fieldset>` with a
  `<legend>`.
- **Data table:** `<caption>` (sr-only), `<th scope="col">` column headers, and
  `<th scope="row">` row headers.
- **Custom widgets:** the occupancy meters use `role="progressbar"` with
  `aria-valuemin/max/now` and an `aria-label`.
- **Landmarks & bypass:** a "Skip to main content" link is the first tab stop;
  `<nav>` and `<main id="main-content">` landmarks are present.
- **Live regions:** result/alert containers use `aria-live="polite"`.
- **Language:** `<html lang="en">`; `aria-current="page"` marks the active nav
  link.
- **HTML text contrast:** all non-SVG text passes axe's `color-contrast` (AA).

## Known limitation (not a WCAG failure of the audited pages)

The AI-phrased copy supports 8 languages including Arabic, but the page layout
is **not RTL-aware** (no `dir="rtl"` switching). This is documented in the
README as a known limitation; the Arabic *text* renders correctly, but bidi
layout mirroring is out of scope for this submission.

## How to re-run

```bash
pytest -m e2e   # runs the axe-core scan (needs: playwright install chromium)
```

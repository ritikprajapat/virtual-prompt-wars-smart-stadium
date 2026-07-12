# Architecture Decision Log

Short rationale for the key technical tradeoffs in MatchDay AI. This complements
the architecture *description* in the README — here we record *why*, not *what*.

1. **FastAPI for the backend.** Async-native (the AI calls are I/O-bound and run
   concurrently), Pydantic request/response validation for free, and automatic
   OpenAPI docs. It lets thin route handlers stay thin while the type system
   enforces payload shapes at the edge.

2. **Server-rendered Jinja2 + vanilla `fetch()` JS, no frontend build step.** The
   UI is a handful of forms and a live dashboard, not an app. Avoiding React/npm
   keeps the whole stack installable with a single `pip install` and removes a
   bundler, lockfile, and transpile step from the critical path — a better fit
   for a hackathon deliverable that judges must run quickly.

3. **Dijkstra for wayfinding, not A\* or an ML model.** The venue graph is tiny
   (dozens of nodes) so shortest-path cost is negligible and A\*'s heuristic buys
   nothing. Dijkstra is exact, deterministic, and trivially testable — we assert
   routes and distances precisely. A learned model would be non-deterministic and
   unjustifiable at this scale.

4. **Step-free routing as an edge filter, not a separate graph.** Accessibility
   routing reuses the same Dijkstra pass with `require_step_free` excluding
   non-step-free edges. One code path, one set of tests, no divergence risk
   between the "normal" and "accessible" route logic.

5. **Rule-based (not ML) sustainability scoring.** The arrival-mode ranking is a
   fixed, transparent low-to-high impact ordering — deliberately *not* a real
   emissions calculation. It is honest about being a nudge, needs no training
   data, and can't produce a misleading precise-looking number. Transparency and
   defensibility beat false precision here.

6. **AI is a phrasing layer, never the decision-maker.** Routing, crowd
   occupancy, facility matching, and impact ranking are all deterministic Python.
   Gemini only turns already-correct data into natural language. This keeps the
   core logic unit-testable and stops the model from inventing facts like
   directions or facility names.

7. **Gemini for the natural-language copy.** The value-add is short, multilingual,
   friendly phrasing (8 languages) — exactly what an LLM is good at, and not worth
   maintaining per-language templates for. `gemini-2.0-flash` is fast and cheap
   enough for per-request calls behind a rate limit.

8. **All Gemini access funneled through one module (`services/gemini.py`).** The
   API key is read once from the environment and never leaves that module. Every
   AI call goes through `ask_gemini`, which centralizes the timeout, empty-response
   handling, and error wrapping — so there is exactly one place to audit for key
   handling and failure behavior.

9. **AI failures fail closed with a generic `502`.** Every AI-calling route wraps
   `ask_gemini` in `try/except RuntimeError` and returns a generic message, never
   the raw exception. A Gemini outage degrades gracefully instead of leaking
   internals or 500ing. The crowd simulator goes further and falls back to a
   static alert message so staff-facing alerts never disappear.

10. **In-memory crowd simulation, no datastore.** The demo needs live-looking gate
    occupancy, not persistence. An in-process `asyncio` loop ticking every 10s is
    enough, keeps deploy stateless (no DB to provision), and is fully controllable
    in tests by injecting a seeded RNG and calling `tick()` directly.

11. **`venue.json` as a static data file, not a database.** The stadium topology
    is fixed reference data. A JSON file loaded once and cached (`lru_cache`) is
    simpler than a DB, versions cleanly in git, and makes the graph easy to inspect
    and tweak.

12. **Railway for deployment.** Zero-config `Procfile` detection, managed HTTPS,
    and dashboard-based environment variables (so `GEMINI_API_KEY` never touches
    the repo) get a FastAPI app to a public URL with minimal ops overhead — the
    right level of infrastructure for a single-service hackathon project.

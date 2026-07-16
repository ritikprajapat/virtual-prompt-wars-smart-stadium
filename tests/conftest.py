import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limiter import limiter
from app.models.venue import Edge, Facility, Gate, Section, Venue, VenueInfo
from app.services.crowd import simulator
from app.services.llm import LLMClient
from app.services.repository import InMemoryVenueRepository


class FakeLLMClient(LLMClient):
    """Deterministic LLMClient double used to prove the injection seam works.

    It phrases nothing via a network call — it returns a canned string — so a
    service handed this client is exercised entirely offline. This is the
    substitutable, injectable counterpart to GeminiClient (Liskov + DIP).
    """

    def __init__(self, canned: str = "Injected fake LLM response.") -> None:
        self.canned = canned
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        """Record the prompt and return the canned response."""
        self.prompts.append(prompt)
        return self.canned


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _reset_crowd_simulator():
    for gate in simulator.gates.values():
        gate.occupancy = 0
        gate.breached = False
    simulator.alerts = {}
    yield


@pytest.fixture
def mock_gemini(monkeypatch):
    async def _fake_ask_gemini(prompt: str) -> str:
        return "Mocked AI response."

    # wayfinding/accessibility/transport/sustainability phrase through the
    # LLMClient abstraction, whose GeminiClient resolves this single source at
    # call time. crowd.py still calls its own module-level ask_gemini directly,
    # so it is patched separately.
    monkeypatch.setattr("app.services.gemini.ask_gemini", _fake_ask_gemini)
    monkeypatch.setattr("app.services.crowd.ask_gemini", _fake_ask_gemini)
    return _fake_ask_gemini


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def synthetic_venue() -> Venue:
    """A small, self-contained venue graph built entirely in memory."""
    return Venue(
        venue=VenueInfo(name="Test Arena", city="Testville", capacity=100),
        gates=[
            Gate(
                id="gate_x",
                name="Gate X",
                direction="north",
                accessible=True,
                status="open",
            )
        ],
        sections=[
            Section(
                id="sec_x",
                name="Section X",
                block="A",
                level=1,
                gate_access=["gate_x"],
                row_range="1-10",
                accessible_seating=True,
                capacity=50,
            )
        ],
        facilities=[
            Facility(
                id="fac_x", type="medical", name="First Aid", level=1, accessible=True
            )
        ],
        edges=[
            Edge(
                from_="gate_x",
                to="sec_x",
                distance_m=10.0,
                walk_time_min=1.0,
                step_free=True,
            )
        ],
    )


@pytest.fixture
def in_memory_venue_repository(synthetic_venue: Venue) -> InMemoryVenueRepository:
    """An InMemoryVenueRepository serving the synthetic venue (no file I/O)."""
    return InMemoryVenueRepository(synthetic_venue)

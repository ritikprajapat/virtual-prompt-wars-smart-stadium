import asyncio
import random

import pytest

from app.services.crowd import ALERT_THRESHOLD, CrowdSimulator, GateState


@pytest.mark.asyncio
async def test_tick_updates_occupancy_within_bounds():
    sim = CrowdSimulator()
    gate = next(iter(sim.gates.values()))
    gate.occupancy = gate.capacity // 2
    await sim.tick(rng=random.Random(42))
    assert 0 <= gate.occupancy <= gate.capacity


@pytest.mark.asyncio
async def test_tick_generates_alert_above_threshold(monkeypatch):
    async def _fake_ask_gemini(prompt: str) -> str:
        return "Reroute suggestion."

    monkeypatch.setattr("app.services.crowd.ask_gemini", _fake_ask_gemini)

    sim = CrowdSimulator()
    gate = next(iter(sim.gates.values()))
    gate.occupancy = int(gate.capacity * ALERT_THRESHOLD)

    class _AlwaysGrow(random.Random):
        def uniform(self, a, b):
            return b

    alerts = await sim.tick(rng=_AlwaysGrow())
    assert len(alerts) >= 1
    assert alerts[0].gate_id == gate.gate_id
    assert alerts[0].occupancy_pct >= ALERT_THRESHOLD


@pytest.mark.asyncio
async def test_tick_falls_back_to_static_message_when_ai_fails(monkeypatch):
    async def _fake_ask_gemini_fails(prompt: str) -> str:
        raise RuntimeError("AI request failed")

    monkeypatch.setattr("app.services.crowd.ask_gemini", _fake_ask_gemini_fails)

    sim = CrowdSimulator()
    gate = next(iter(sim.gates.values()))
    gate.occupancy = gate.capacity

    class _AlwaysGrow(random.Random):
        def uniform(self, a, b):
            return b

    alerts = await sim.tick(rng=_AlwaysGrow())
    assert len(alerts) >= 1
    assert "capacity" in alerts[0].message


@pytest.mark.asyncio
async def test_sustained_breach_does_not_regenerate_alert(monkeypatch):
    call_count = 0

    async def _fake_ask_gemini(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        return "Reroute suggestion."

    monkeypatch.setattr("app.services.crowd.ask_gemini", _fake_ask_gemini)

    sim = CrowdSimulator()
    gate = next(iter(sim.gates.values()))
    gate.occupancy = int(gate.capacity * ALERT_THRESHOLD)

    class _StayFlat(random.Random):
        def uniform(self, a, b):
            return 0.0

    first_tick_alerts = await sim.tick(rng=_StayFlat())
    second_tick_alerts = await sim.tick(rng=_StayFlat())

    assert len(first_tick_alerts) == 1
    assert call_count == 1
    assert second_tick_alerts == []
    assert call_count == 1
    assert len(sim.active_alerts()) == 1


@pytest.mark.asyncio
async def test_alert_clears_once_gate_drops_below_threshold(monkeypatch):
    async def _fake_ask_gemini(prompt: str) -> str:
        return "Reroute suggestion."

    monkeypatch.setattr("app.services.crowd.ask_gemini", _fake_ask_gemini)

    sim = CrowdSimulator()
    gate = next(iter(sim.gates.values()))
    gate.occupancy = int(gate.capacity * ALERT_THRESHOLD)

    class _StayFlat(random.Random):
        def uniform(self, a, b):
            return 0.0

    await sim.tick(rng=_StayFlat())
    assert len(sim.active_alerts()) == 1

    gate.occupancy = 0
    await sim.tick(rng=_StayFlat())
    assert sim.active_alerts() == []


def test_pre_seeded_gates_are_left_untouched():
    # When gates are supplied, __post_init__ must not overwrite them from venue.json.
    seeded = {"g1": GateState(gate_id="g1", name="Custom Gate", capacity=100)}
    sim = CrowdSimulator(gates=seeded)
    assert sim.gates is seeded
    assert list(sim.gates) == ["g1"]


def test_occupancy_pct_is_zero_when_capacity_is_zero():
    gate = GateState(gate_id="g", name="G", capacity=0, occupancy=5)
    assert gate.occupancy_pct == 0.0


@pytest.mark.asyncio
async def test_background_loop_start_is_idempotent_and_stops_cleanly():
    sim = CrowdSimulator(gates={"g": GateState(gate_id="g", name="G", capacity=10)})

    # Stopping when nothing is running is a no-op.
    sim.stop_background_loop()
    assert sim._task is None

    sim.start_background_loop()
    first_task = sim._task
    assert first_task is not None

    # Calling start again while running must not replace the existing task.
    sim.start_background_loop()
    assert sim._task is first_task

    sim.stop_background_loop()
    assert sim._task is None
    await asyncio.sleep(0)  # let the cancellation settle


def test_crowd_status_endpoint_returns_snapshot(client):
    response = client.get("/api/crowd/status")
    assert response.status_code == 200
    body = response.json()
    assert "gates" in body
    assert "alerts" in body
    assert len(body["gates"]) > 0

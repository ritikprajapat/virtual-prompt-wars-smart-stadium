"""Live gate occupancy simulation with AI-generated reroute alerts at high occupancy.

The simulation advances on a background task on a fixed interval rather than on
each request so that occupancy evolves as real wall-clock time passes and every
client sees the same shared state, independent of who happens to poll. Ticking
on-request would instead tie the crowd's movement to request volume and give
each caller a divergent view. The alert phrasing falls back to a static message
when the AI call fails, so a Gemini outage degrades wording, never the alert.
"""
import asyncio
import random
from dataclasses import dataclass, field

from app.services.gemini import ask_gemini
from app.services.venue_repository import load_venue

ALERT_THRESHOLD = 0.85
TICK_SECONDS = 10


@dataclass
class GateState:
    """Live occupancy state for a single gate."""

    gate_id: str
    name: str
    capacity: int
    occupancy: int = 0
    breached: bool = False

    @property
    def occupancy_pct(self) -> float:
        """Current occupancy as a fraction of capacity (0.0 if capacity is zero)."""
        return round(self.occupancy / self.capacity, 3) if self.capacity else 0.0


@dataclass
class CrowdAlert:
    """A staff-facing alert for a gate that has crossed the occupancy threshold."""

    gate_id: str
    gate_name: str
    occupancy_pct: float
    message: str


@dataclass
class CrowdSimulator:
    """In-memory simulation of gate occupancy that raises alerts on breaches."""

    gates: dict[str, GateState] = field(default_factory=dict)
    alerts: dict[str, CrowdAlert] = field(default_factory=dict)
    _task: asyncio.Task[None] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Seed one GateState per venue gate, splitting capacity evenly."""
        if self.gates:
            return
        venue = load_venue()
        per_gate_capacity = max(venue.venue.capacity // max(len(venue.gates), 1), 1)
        for gate in venue.gates:
            self.gates[gate.id] = GateState(
                gate_id=gate.id, name=gate.name, capacity=per_gate_capacity
            )

    def snapshot(self) -> list[dict[str, object]]:
        """Return a serializable occupancy snapshot for every gate."""
        return [
            {
                "gate_id": g.gate_id,
                "name": g.name,
                "capacity": g.capacity,
                "occupancy": g.occupancy,
                "occupancy_pct": g.occupancy_pct,
            }
            for g in self.gates.values()
        ]

    def active_alerts(self) -> list[CrowdAlert]:
        """One alert per currently over-threshold gate, most severe first."""
        return sorted(self.alerts.values(), key=lambda a: a.occupancy_pct, reverse=True)

    async def tick(self, rng: random.Random | None = None) -> list[CrowdAlert]:
        """Advance the simulation one step; return alerts for newly breached gates."""
        uniform = rng.uniform if rng is not None else random.uniform
        new_alerts: list[CrowdAlert] = []
        for gate in self.gates.values():
            delta = int(gate.capacity * uniform(-0.05, 0.12))
            gate.occupancy = max(0, min(gate.capacity, gate.occupancy + delta))
            if gate.occupancy_pct >= ALERT_THRESHOLD:
                if gate.breached:
                    self.alerts[gate.gate_id].occupancy_pct = gate.occupancy_pct
                else:
                    gate.breached = True
                    alert = await self._build_alert(gate)
                    self.alerts[gate.gate_id] = alert
                    new_alerts.append(alert)
            else:
                gate.breached = False
                self.alerts.pop(gate.gate_id, None)
        return new_alerts

    async def _build_alert(self, gate: GateState) -> CrowdAlert:
        """Draft an alert for a breached gate, falling back to a static message."""
        prompt = (
            f"Stadium gate '{gate.name}' is at "
            f"{round(gate.occupancy_pct * 100)}% capacity. "
            f"In one short sentence, suggest a reroute or staffing action for "
            f"stadium operations staff."
        )
        try:
            message = await ask_gemini(prompt)
        except RuntimeError:
            message = (
                f"{gate.name} is over {int(ALERT_THRESHOLD * 100)}% capacity — "
                f"consider rerouting arrivals to an adjacent gate."
            )
        return CrowdAlert(
            gate_id=gate.gate_id,
            gate_name=gate.name,
            occupancy_pct=gate.occupancy_pct,
            message=message,
        )

    async def run_forever(self) -> None:
        """Continuously tick the simulation on a fixed interval."""
        while True:
            await self.tick()
            await asyncio.sleep(TICK_SECONDS)

    def start_background_loop(self) -> None:
        """Start the background tick loop if it is not already running."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_forever())

    def stop_background_loop(self) -> None:
        """Cancel the background tick loop if one is running."""
        if self._task is not None:
            self._task.cancel()
            self._task = None


simulator = CrowdSimulator()

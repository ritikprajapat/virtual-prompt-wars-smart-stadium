"""Live gate occupancy simulation with AI-generated reroute alerts at high occupancy."""
import asyncio
import random
from dataclasses import dataclass, field

from app.services.gemini import ask_gemini
from app.services.venue_repository import load_venue

ALERT_THRESHOLD = 0.85
TICK_SECONDS = 10


@dataclass
class GateState:
    gate_id: str
    name: str
    capacity: int
    occupancy: int = 0
    breached: bool = False

    @property
    def occupancy_pct(self) -> float:
        return round(self.occupancy / self.capacity, 3) if self.capacity else 0.0


@dataclass
class CrowdAlert:
    gate_id: str
    gate_name: str
    occupancy_pct: float
    message: str


@dataclass
class CrowdSimulator:
    gates: dict[str, GateState] = field(default_factory=dict)
    alerts: dict[str, CrowdAlert] = field(default_factory=dict)
    _task: asyncio.Task | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.gates:
            return
        venue = load_venue()
        per_gate_capacity = max(venue.venue.capacity // max(len(venue.gates), 1), 1)
        for gate in venue.gates:
            self.gates[gate.id] = GateState(gate_id=gate.id, name=gate.name, capacity=per_gate_capacity)

    def snapshot(self) -> list[dict]:
        return [
            {"gate_id": g.gate_id, "name": g.name, "capacity": g.capacity, "occupancy": g.occupancy, "occupancy_pct": g.occupancy_pct}
            for g in self.gates.values()
        ]

    def active_alerts(self) -> list[CrowdAlert]:
        """One alert per currently over-threshold gate, most severe first."""
        return sorted(self.alerts.values(), key=lambda a: a.occupancy_pct, reverse=True)

    async def tick(self, rng: random.Random | None = None) -> list[CrowdAlert]:
        """Advance the simulation by one step and return alerts for gates newly crossing the threshold."""
        rng = rng or random
        new_alerts: list[CrowdAlert] = []
        for gate in self.gates.values():
            delta = int(gate.capacity * rng.uniform(-0.05, 0.12))
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
        prompt = (
            f"Stadium gate '{gate.name}' is at {round(gate.occupancy_pct * 100)}% capacity. "
            f"In one short sentence, suggest a reroute or staffing action for stadium operations staff."
        )
        try:
            message = await ask_gemini(prompt)
        except RuntimeError:
            message = f"{gate.name} is over {int(ALERT_THRESHOLD * 100)}% capacity — consider rerouting arrivals to an adjacent gate."
        return CrowdAlert(gate_id=gate.gate_id, gate_name=gate.name, occupancy_pct=gate.occupancy_pct, message=message)

    async def run_forever(self) -> None:
        while True:
            await self.tick()
            await asyncio.sleep(TICK_SECONDS)

    def start_background_loop(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_forever())

    def stop_background_loop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None


simulator = CrowdSimulator()

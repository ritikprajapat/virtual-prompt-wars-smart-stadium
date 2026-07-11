(function () {
  const clockEl = document.getElementById("hero-clock");
  if (clockEl) {
    const kickoff = (() => {
      const d = new Date();
      d.setHours(19, 0, 0, 0);
      if (d < new Date()) d.setDate(d.getDate() + 1);
      return d;
    })();
    const tick = () => {
      const diff = Math.max(0, kickoff - new Date());
      const h = String(Math.floor(diff / 3600000)).padStart(2, "0");
      const m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
      const s = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");
      clockEl.textContent = `${h}:${m}:${s}`;
    };
    tick();
    setInterval(tick, 1000);
  }

  const svg = document.getElementById("mini-map");
  if (!svg) return;

  const POLL_INTERVAL_MS = 5000;

  const GATE_LAYOUT = {
    gate_a: { short: "A", angle: -90 },
    gate_b: { short: "B", angle: -18 },
    gate_c: { short: "C", angle: 54 },
    gate_d: { short: "D", angle: 198 },
    gate_acc: { short: "ADA", angle: 126 },
  };

  function layoutFor(gateId, index, total) {
    if (GATE_LAYOUT[gateId]) return GATE_LAYOUT[gateId];
    return { short: gateId.slice(0, 3).toUpperCase(), angle: (360 / total) * index - 90 };
  }

  function severityColor(pct) {
    if (pct >= 85) return "var(--coral)";
    if (pct >= 50) return "var(--gold)";
    return "var(--pitch)";
  }

  function render(gates) {
    const cx = 150;
    const cy = 85;
    const rx = 95;
    const ry = 44;
    let markup = `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="none" stroke="var(--color-border)" stroke-width="1.2"/>
      <circle cx="${cx}" cy="${cy}" r="14" fill="none" stroke="var(--color-border)" stroke-width="1"/>`;

    gates.forEach((gate, index) => {
      const layout = layoutFor(gate.gate_id, index, gates.length);
      const rad = (layout.angle * Math.PI) / 180;
      const nx = cx + Math.cos(rad) * (rx + 22);
      const ny = cy + Math.sin(rad) * (ry + 22);
      const pct = Math.round(gate.occupancy_pct * 100);
      const color = severityColor(pct);
      const r = 7 + (pct / 100) * 7;
      const labelY = ny > cy ? ny + 15 : ny - 10;
      markup += `<line x1="${cx + Math.cos(rad) * rx}" y1="${cy + Math.sin(rad) * ry}" x2="${nx}" y2="${ny}" stroke="var(--color-border)" stroke-width="1"/>
        <circle class="node" data-gate-id="${gate.gate_id}" data-name="${gate.name}" cx="${nx}" cy="${ny}" r="${r}" fill="${color}" style="cursor:pointer;">
          <title>${gate.name}: ${pct}% full</title>
        </circle>
        <text class="node-label" x="${nx}" y="${labelY}" text-anchor="middle">${layout.short}</text>`;
    });

    svg.innerHTML = markup;
    svg.querySelectorAll(".node").forEach((node) => {
      node.addEventListener("click", () => {
        const destSelect = document.getElementById("target_node_id");
        if (!destSelect) return;
        destSelect.value = node.dataset.gateId;
        destSelect.closest(".gate").scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }

  async function refresh() {
    try {
      const response = await fetch("/api/crowd/status");
      if (!response.ok) return;
      const data = await response.json();
      render(data.gates);
    } catch (err) {
      /* leave the last known map in place on a transient network error */
    }
  }

  refresh();
  setInterval(refresh, POLL_INTERVAL_MS);
})();

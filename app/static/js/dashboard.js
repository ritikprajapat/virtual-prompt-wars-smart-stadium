(function () {
  const tbody = document.getElementById("occupancy-tbody");
  const alertsList = document.getElementById("alerts-list");
  const tickButton = document.getElementById("advance-tick");
  const chartWrap = document.getElementById("trend-chart");
  const stadiumMap = document.getElementById("stadium-map");
  const kpiTotal = document.getElementById("kpi-total");
  const kpiTotalSub = document.getElementById("kpi-total-sub");
  const kpiAvg = document.getElementById("kpi-avg");
  const kpiAvgCard = document.getElementById("kpi-avg-card");
  const kpiRisk = document.getElementById("kpi-risk");
  const kpiRiskCard = document.getElementById("kpi-risk-card");
  const kpiPeak = document.getElementById("kpi-peak");
  const kpiPeakSub = document.getElementById("kpi-peak-sub");
  const POLL_INTERVAL_MS = 5000;
  const SPARK_MAX_POINTS = 8;

  if (!tbody) return;

  function severityClass(pct) {
    if (pct >= 85) return "severity-high";
    if (pct >= 50) return "severity-medium";
    return "severity-low";
  }

  const TONE_BY_SEVERITY = { "severity-high": "coral", "severity-medium": "gold", "severity-low": "pitch" };
  function toneForPct(pct) {
    return TONE_BY_SEVERITY[severityClass(pct)];
  }

  // Catmull-Rom-to-Bezier smoothing so trend lines read as curves, not jagged zigzags.
  function smoothPath(coords) {
    if (coords.length < 3) {
      return coords.map((c, i) => (i === 0 ? "M" : "L") + c[0].toFixed(1) + "," + c[1].toFixed(1)).join(" ");
    }
    let d = `M${coords[0][0].toFixed(1)},${coords[0][1].toFixed(1)}`;
    for (let i = 0; i < coords.length - 1; i++) {
      const p0 = coords[i - 1] || coords[i];
      const p1 = coords[i];
      const p2 = coords[i + 1];
      const p3 = coords[i + 2] || p2;
      const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
      const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
      const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
      const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += ` C${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
    }
    return d;
  }

  function buildCheckIcon() {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "14");
    svg.setAttribute("height", "14");
    svg.setAttribute("fill", "none");
    svg.setAttribute("aria-hidden", "true");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", "M20 6L9 17l-5-5");
    path.setAttribute("stroke", "currentColor");
    path.setAttribute("stroke-width", "2.5");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");
    svg.appendChild(path);
    return svg;
  }

  // --- Gate manifest table: segmented occupancy bar + per-row sparkline. ---

  const sparkHistory = {}; // gate_id -> number[] (last SPARK_MAX_POINTS occupancy pct values)

  function sparklineMarkup(points, color) {
    const w = 68;
    const h = 24;
    const pad = 2;
    if (points.length < 2) return "";
    const min = Math.min(...points);
    const max = Math.max(...points, min + 1);
    const stepX = (w - pad * 2) / (points.length - 1);
    const coords = points.map((v, i) => {
      const x = pad + i * stepX;
      const y = h - pad - ((v - min) / (max - min)) * (h - pad * 2);
      return [x, y];
    });
    const d = smoothPath(coords);
    const last = coords[coords.length - 1];
    return (
      `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">` +
      `<path d="${d}" fill="none" stroke="${color}" stroke-width="1.6"/>` +
      `<circle cx="${last[0]}" cy="${last[1]}" r="2.2" fill="${color}"/>` +
      `</svg>`
    );
  }

  function renderGates(gates) {
    gates.forEach((gate) => {
      const row = tbody.querySelector(`tr[data-gate-id="${gate.gate_id}"]`);
      if (!row) return;
      const pct = Math.round(gate.occupancy_pct * 100);
      row.querySelector(".occ-value").textContent = gate.occupancy.toLocaleString();
      row.querySelector(".cap-value").textContent = gate.capacity.toLocaleString();
      row.querySelector(".pct-value").textContent = `${pct}%`;

      const segBar = row.querySelector(".segbar");
      segBar.setAttribute("aria-valuenow", String(pct));
      segBar.className = `segbar ${severityClass(pct)}`;
      const onSegments = Math.round(pct / 10);
      segBar.querySelectorAll("i").forEach((seg, index) => {
        seg.classList.toggle("on", index < onSegments);
      });

      const history = sparkHistory[gate.gate_id] || (sparkHistory[gate.gate_id] = []);
      history.push(pct);
      if (history.length > SPARK_MAX_POINTS) history.shift();
      const sparkCell = row.querySelector(".spark-cell");
      if (sparkCell) {
        const color = getComputedStyle(document.documentElement)
          .getPropertyValue(`--color-${toneForPct(pct) === "pitch" ? "success" : toneForPct(pct) === "gold" ? "warning" : "danger"}`)
          .trim();
        sparkCell.innerHTML = sparklineMarkup(history, color);
      }
    });
  }

  // --- KPI strip: derived entirely from the live gate snapshot, no invented figures. ---

  function renderKPIs(gates) {
    if (!kpiTotal) return;
    const totalOccupancy = gates.reduce((sum, g) => sum + g.occupancy, 0);
    const totalCapacity = gates.reduce((sum, g) => sum + g.capacity, 0);
    const avgPct = Math.round(gates.reduce((sum, g) => sum + g.occupancy_pct * 100, 0) / gates.length);
    const atRisk = gates.filter((g) => g.occupancy_pct * 100 >= 85).length;
    const peak = gates.reduce((max, g) => (g.occupancy_pct > max.occupancy_pct ? g : max), gates[0]);
    const peakPct = Math.round(peak.occupancy_pct * 100);

    kpiTotal.textContent = totalOccupancy.toLocaleString();
    kpiTotalSub.textContent = `of ${totalCapacity.toLocaleString()} capacity`;
    kpiAvg.textContent = `${avgPct}%`;
    kpiAvgCard.dataset.tone = toneForPct(avgPct);
    kpiRisk.textContent = String(atRisk);
    kpiRiskCard.dataset.tone = atRisk > 0 ? "coral" : "pitch";
    kpiPeak.textContent = peak.name.replace(/^Gate\s+/, "");
    kpiPeakSub.textContent = `at ${peakPct}% full`;
  }

  // --- Stadium map: gate nodes placed by their real compass direction, sized/colored by live load. ---

  const DIRECTION_ANGLE = {
    North: -90,
    Northeast: -45,
    East: 0,
    Southeast: 45,
    South: 90,
    Southwest: 135,
    West: 180,
    Northwest: -135,
  };

  const mapNodes = Array.from(tbody.querySelectorAll("tr")).map((row) => ({
    gate_id: row.dataset.gateId,
    name: row.querySelector("th").textContent,
    angle: DIRECTION_ANGLE[row.dataset.direction] ?? 0,
  }));

  function renderMap(gates) {
    if (!stadiumMap) return;
    const cx = 200;
    const cy = 120;
    const rx = 140;
    const ry = 58;
    const outerPad = 22;
    const gateById = Object.fromEntries(gates.map((g) => [g.gate_id, g]));

    let markup = `
      <ellipse cx="${cx}" cy="${cy}" rx="${rx + outerPad}" ry="${ry + outerPad}" fill="none" stroke="var(--color-border)" stroke-width="1" stroke-dasharray="3 5"/>
      <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="color-mix(in srgb, var(--color-primary) 10%, transparent)" stroke="var(--color-border)" stroke-width="1.4"/>
      <line x1="${cx}" y1="${cy - ry}" x2="${cx}" y2="${cy + ry}" stroke="var(--color-border)" stroke-width="1"/>
      <circle cx="${cx}" cy="${cy}" r="18" fill="none" stroke="var(--color-border)" stroke-width="1"/>
      <g class="sweep" style="transform-origin:${cx}px ${cy}px" opacity="0.5">
        <line x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy - ry}" stroke="var(--color-primary)" stroke-width="1.4"/>
      </g>`;

    mapNodes.forEach((node) => {
      const gate = gateById[node.gate_id];
      if (!gate) return;
      const pct = Math.round(gate.occupancy_pct * 100);
      const rad = (node.angle * Math.PI) / 180;
      const nx = cx + Math.cos(rad) * (rx + outerPad);
      const ny = cy + Math.sin(rad) * (ry + outerPad);
      const color = `var(--color-${toneForPct(pct) === "pitch" ? "success" : toneForPct(pct) === "gold" ? "warning" : "danger"})`;
      const r = 9 + (pct / 100) * 9;
      const below = ny > cy + 4;
      const labelY = below ? ny + 20 : ny - 16;
      const shortCode = node.gate_id.replace(/^gate_/, "").toUpperCase();
      markup += `
        <line x1="${cx + Math.cos(rad) * rx}" y1="${cy + Math.sin(rad) * ry}" x2="${nx}" y2="${ny}" stroke="var(--color-border)" stroke-width="1"/>
        <circle cx="${nx}" cy="${ny}" r="${r + 6}" fill="${color}" opacity="0.16"/>
        <circle cx="${nx}" cy="${ny}" r="${r}" fill="${color}"/>
        <text class="node-label" x="${nx}" y="${labelY}" text-anchor="middle">${shortCode}</text>
        <text class="node-pct" x="${nx}" y="${labelY + (below ? 13 : -13)}" text-anchor="middle" fill="${color}">${pct}%</text>`;
    });

    stadiumMap.innerHTML = markup;
  }

  // --- Operations feed: logs a new entry only when a gate newly crosses the alert threshold. ---

  const feedEntries = [];
  let previousAlertIds = new Set();
  const FEED_MAX_ENTRIES = 8;

  function pushFeedEntries(alerts) {
    const stamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    alerts.forEach((alert) => {
      const pct = Math.round(alert.occupancy_pct * 100);
      feedEntries.unshift({
        time: stamp,
        severity: severityClass(pct),
        title: `${alert.gate_name} at ${pct}% capacity`,
        detail: alert.message,
      });
    });
    if (feedEntries.length > FEED_MAX_ENTRIES) feedEntries.length = FEED_MAX_ENTRIES;
    renderFeed();
  }

  function renderFeed() {
    alertsList.innerHTML = "";
    if (!feedEntries.length) {
      const empty = document.createElement("div");
      empty.className = "no-alert";
      empty.appendChild(buildCheckIcon());
      const label = document.createElement("span");
      label.textContent = "No active alerts";
      empty.appendChild(label);
      alertsList.appendChild(empty);
      return;
    }
    // Built via DOM + textContent (not innerHTML): the alert title and detail
    // include a gate name and AI-generated text, so they must never be parsed
    // as markup.
    feedEntries.forEach((entry) => {
      const tone =
        entry.severity === "severity-high"
          ? "danger"
          : entry.severity === "severity-medium"
          ? "warning"
          : "success";

      const row = document.createElement("div");
      row.className = "log-row";

      const time = document.createElement("div");
      time.className = "log-time mono";
      time.textContent = entry.time;

      const dot = document.createElement("div");
      dot.className = "log-dot";
      dot.style.background = `var(--color-${tone})`;

      const body = document.createElement("div");
      body.className = "log-body";
      const title = document.createElement("b");
      title.textContent = entry.title;
      const detail = document.createElement("span");
      detail.textContent = entry.detail;
      body.append(title, detail);

      row.append(time, dot, body);
      alertsList.appendChild(row);
    });
  }

  function updateAlerts(currentAlerts) {
    const currentIds = new Set(currentAlerts.map((a) => a.gate_id));
    const newlyBreached = currentAlerts.filter((a) => !previousAlertIds.has(a.gate_id));
    if (newlyBreached.length) pushFeedEntries(newlyBreached);
    previousAlertIds = currentIds;
  }

  const trendChart = chartWrap ? createTrendChart(chartWrap) : null;

  async function refresh() {
    try {
      const response = await fetch("/api/crowd/status");
      if (!response.ok) return;
      const data = await response.json();
      renderGates(data.gates);
      renderKPIs(data.gates);
      renderMap(data.gates);
      updateAlerts(data.alerts);
      if (trendChart) trendChart.push(data.gates);
    } catch {
      // Silently skip this poll; the next interval will retry.
    }
  }

  if (tickButton) {
    tickButton.addEventListener("click", async () => {
      tickButton.disabled = true;
      try {
        const response = await fetch("/api/crowd/simulate-tick", { method: "POST" });
        if (response.ok) {
          const data = await response.json();
          renderGates(data.gates);
          renderKPIs(data.gates);
          renderMap(data.gates);
          if (data.new_alerts.length) {
            pushFeedEntries(data.new_alerts);
            data.new_alerts.forEach((a) => previousAlertIds.add(a.gate_id));
          }
        }
      } finally {
        tickButton.disabled = false;
        refresh();
      }
    });
  }

  renderFeed();
  refresh();
  setInterval(refresh, POLL_INTERVAL_MS);

  // --- Occupancy trend chart: inline SVG, no chart library, CSP-friendly. ---

  function createTrendChart(root) {
    const MAX_POINTS = 30;
    const WIDTH = 640;
    const HEIGHT = 220;
    const PAD = { top: 12, right: 12, bottom: 8, left: 32 };
    const SERIES_VARS = ["--series-1", "--series-2", "--series-3", "--series-4", "--series-5"];

    const samples = []; // [{ values: { gate_id: pct }, at: Date.now() }]
    let seriesOrder = null; // [{ gate_id, name }] fixed after first sample

    // Decorative/supplementary: the occupancy table above is the accessible data source.
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "chart-svg");
    svg.setAttribute("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);
    svg.setAttribute("aria-hidden", "true");
    root.appendChild(svg);

    const legend = document.createElement("ul");
    legend.className = "chart-legend";
    root.appendChild(legend);

    const tooltip = document.createElement("div");
    tooltip.className = "chart-tooltip";
    root.appendChild(tooltip);

    let hitLayer = null;
    let crosshair = null;
    let focusedIndex = null;

    function seriesColor(index) {
      return getComputedStyle(document.documentElement).getPropertyValue(SERIES_VARS[index % SERIES_VARS.length]).trim();
    }

    function xFor(index, count) {
      if (count <= 1) return PAD.left;
      const usableWidth = WIDTH - PAD.left - PAD.right;
      return PAD.left + (usableWidth * index) / (count - 1);
    }

    function yFor(pct) {
      const usableHeight = HEIGHT - PAD.top - PAD.bottom;
      return PAD.top + usableHeight * (1 - pct / 100);
    }

    function buildLegend() {
      legend.innerHTML = "";
      seriesOrder.forEach((series, index) => {
        const li = document.createElement("li");
        const swatch = document.createElement("span");
        swatch.className = "legend-swatch";
        swatch.style.background = seriesColor(index);
        li.appendChild(swatch);
        li.appendChild(document.createTextNode(series.name));
        legend.appendChild(li);
      });
    }

    function showTooltip(index) {
      const sample = samples[index];
      if (!sample) return;
      tooltip.innerHTML = "";

      const timeEl = document.createElement("p");
      timeEl.className = "chart-tooltip-time";
      const secondsAgo = Math.round((Date.now() - sample.at) / 1000);
      timeEl.textContent = secondsAgo <= 1 ? "Just now" : `${secondsAgo}s ago`;
      tooltip.appendChild(timeEl);

      seriesOrder.forEach((series, i) => {
        const row = document.createElement("div");
        row.className = "chart-tooltip-row";
        const swatch = document.createElement("span");
        swatch.className = "legend-swatch";
        swatch.style.background = seriesColor(i);
        row.appendChild(swatch);
        row.appendChild(document.createTextNode(series.name));
        const value = document.createElement("span");
        value.className = "chart-tooltip-value";
        const pct = sample.values[series.gate_id];
        value.textContent = pct == null ? "—" : `${pct}%`;
        row.appendChild(value);
        tooltip.appendChild(row);
      });

      const count = samples.length;
      const x = xFor(index, count);
      const bounds = root.getBoundingClientRect();
      const svgBounds = svg.getBoundingClientRect();
      const scale = svgBounds.width / WIDTH;
      const left = svgBounds.left - bounds.left + x * scale;
      tooltip.style.transform = `translate(${Math.min(Math.max(left, 4), bounds.width - 4)}px, 4px)`;

      if (crosshair) {
        crosshair.setAttribute("x1", String(x));
        crosshair.setAttribute("x2", String(x));
        crosshair.style.opacity = "1";
      }
    }

    function hideTooltip() {
      tooltip.style.transform = "translate(-9999px, -9999px)";
      if (crosshair) crosshair.style.opacity = "0";
    }

    function nearestIndexForClientX(clientX) {
      const svgBounds = svg.getBoundingClientRect();
      const scale = WIDTH / svgBounds.width;
      const localX = (clientX - svgBounds.left) * scale;
      const count = samples.length;
      if (count <= 1) return 0;
      const usableWidth = WIDTH - PAD.left - PAD.right;
      const ratio = Math.min(Math.max((localX - PAD.left) / usableWidth, 0), 1);
      return Math.round(ratio * (count - 1));
    }

    function render() {
      svg.innerHTML = "";
      const count = samples.length;

      if (count < 2 || !seriesOrder) {
        const empty = document.createElementNS("http://www.w3.org/2000/svg", "text");
        empty.setAttribute("x", String(WIDTH / 2));
        empty.setAttribute("y", String(HEIGHT / 2));
        empty.setAttribute("text-anchor", "middle");
        empty.setAttribute("class", "chart-axis-label");
        empty.textContent = "Gathering data…";
        svg.appendChild(empty);
        hideTooltip();
        return;
      }

      const gridGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      [0, 25, 50, 75, 100].forEach((tick) => {
        const y = yFor(tick);
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("class", "chart-gridline");
        line.setAttribute("x1", String(PAD.left));
        line.setAttribute("x2", String(WIDTH - PAD.right));
        line.setAttribute("y1", String(y));
        line.setAttribute("y2", String(y));
        gridGroup.appendChild(line);

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("class", "chart-axis-label");
        label.setAttribute("x", "0");
        label.setAttribute("y", String(y + 3));
        label.textContent = `${tick}`;
        gridGroup.appendChild(label);
      });
      svg.appendChild(gridGroup);

      const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
      svg.appendChild(defs);
      const baseline = HEIGHT - PAD.bottom;

      seriesOrder.forEach((series, seriesIndex) => {
        const coords = samples
          .map((sample, i) => {
            const pct = sample.values[series.gate_id];
            return pct == null ? null : [xFor(i, count), yFor(pct)];
          })
          .filter(Boolean);
        if (!coords.length) return;

        const color = seriesColor(seriesIndex);
        const gradientId = `trend-gradient-${seriesIndex}`;
        const gradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
        gradient.setAttribute("id", gradientId);
        gradient.setAttribute("x1", "0");
        gradient.setAttribute("y1", "0");
        gradient.setAttribute("x2", "0");
        gradient.setAttribute("y2", "1");
        gradient.innerHTML = `<stop offset="0%" stop-color="${color}" stop-opacity="0.28"/><stop offset="100%" stop-color="${color}" stop-opacity="0"/>`;
        defs.appendChild(gradient);

        const linePath = smoothPath(coords);
        const areaPath = `${linePath} L${coords[coords.length - 1][0]},${baseline} L${coords[0][0]},${baseline} Z`;

        const area = document.createElementNS("http://www.w3.org/2000/svg", "path");
        area.setAttribute("class", "chart-area");
        area.setAttribute("d", areaPath);
        area.setAttribute("fill", `url(#${gradientId})`);
        svg.appendChild(area);

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "chart-line");
        path.setAttribute("d", linePath);
        path.setAttribute("stroke", color);
        svg.appendChild(path);

        const lastSample = samples[count - 1];
        const lastPct = lastSample.values[series.gate_id];
        if (lastPct != null) {
          const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          dot.setAttribute("class", "chart-end-dot");
          dot.setAttribute("cx", String(xFor(count - 1, count)));
          dot.setAttribute("cy", String(yFor(lastPct)));
          dot.setAttribute("r", "4");
          dot.setAttribute("fill", color);
          svg.appendChild(dot);
        }
      });

      crosshair = document.createElementNS("http://www.w3.org/2000/svg", "line");
      crosshair.setAttribute("class", "chart-crosshair");
      crosshair.setAttribute("y1", String(PAD.top));
      crosshair.setAttribute("y2", String(HEIGHT - PAD.bottom));
      svg.appendChild(crosshair);

      hitLayer = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      hitLayer.setAttribute("class", "chart-hit-layer");
      hitLayer.setAttribute("x", "0");
      hitLayer.setAttribute("y", "0");
      hitLayer.setAttribute("width", String(WIDTH));
      hitLayer.setAttribute("height", String(HEIGHT));
      hitLayer.addEventListener("pointermove", (event) => {
        focusedIndex = nearestIndexForClientX(event.clientX);
        showTooltip(focusedIndex);
      });
      hitLayer.addEventListener("pointerleave", () => {
        focusedIndex = null;
        hideTooltip();
      });
      svg.appendChild(hitLayer);
    }

    return {
      push(gates) {
        if (!seriesOrder) {
          seriesOrder = gates.map((g) => ({ gate_id: g.gate_id, name: g.name }));
          buildLegend();
        }
        const values = {};
        gates.forEach((g) => {
          values[g.gate_id] = Math.round(g.occupancy_pct * 100);
        });
        samples.push({ values, at: Date.now() });
        if (samples.length > MAX_POINTS) samples.shift();
        render();
      },
    };
  }
})();

(function () {
  const form = document.getElementById("sustainability-form");
  const statusEl = document.getElementById("sustainability-status");
  const resultEl = document.getElementById("sustainability-result");
  const barsEl = document.getElementById("sustainability-bars");
  const badgeEl = document.getElementById("sustainability-badge");

  if (!form) return;

  const IMPACT_ORDER = ["walk_bike", "public_transit", "rideshare", "personal_car"];
  const MODE_LABELS = {
    walk_bike: "Walk / Bike",
    public_transit: "Public transit",
    rideshare: "Rideshare / Taxi",
    personal_car: "Personal car",
  };
  const MODE_COLORS = {
    walk_bike: "var(--pitch)",
    public_transit: "var(--series-1)",
    rideshare: "var(--gold)",
    personal_car: "var(--coral)",
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusEl.classList.remove("error");
    statusEl.textContent = "Comparing your options...";
    resultEl.classList.remove("show");

    const mode = form.mode.value;
    const payload = {
      start_node_id: form.start_node_id.value,
      mode,
      language: "en",
    };

    try {
      const data = await window.MatchDay.postJson(
        "/api/sustainability/advise",
        payload,
        "Could not get a recommendation. Please try again."
      );
      statusEl.textContent = "Here's our recommendation:";

      barsEl.innerHTML = IMPACT_ORDER.map((m, index) => {
        const rank = index + 1;
        const active = m === mode;
        return `<div class="co2row">
          <div class="co2label" style="${active ? "color:var(--color-text);font-weight:600" : ""}">${MODE_LABELS[m]}</div>
          <div class="co2track"><div class="co2fill" style="width:${(rank / IMPACT_ORDER.length) * 100}%;background:${MODE_COLORS[m]}"></div></div>
          <div class="co2val">RANK ${rank}/${IMPACT_ORDER.length}</div>
        </div>`;
      }).join("");

      const rank = data.comparison.impact_rank;
      const tone = rank === 1 ? "pitch" : rank === IMPACT_ORDER.length ? "coral" : "gold";
      badgeEl.textContent = data.guidance;
      badgeEl.style.background = `var(--${tone})`;
      resultEl.classList.add("show");
    } catch (err) {
      statusEl.classList.add("error");
      statusEl.textContent = err.message || "Something went wrong. Please try again.";
    }
  });
})();

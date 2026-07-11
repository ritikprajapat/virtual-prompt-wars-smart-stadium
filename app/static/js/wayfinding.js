(function () {
  const form = document.getElementById("wayfinding-form");
  const statusEl = document.getElementById("wayfinding-status");
  const resultEl = document.getElementById("wayfinding-result");
  const titleEl = document.getElementById("wayfinding-result-title");
  const distEl = document.getElementById("wayfinding-dist");
  const timeEl = document.getElementById("wayfinding-time");
  const stepsEl = document.getElementById("wayfinding-steps");
  const directionsEl = document.getElementById("wayfinding-directions");

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusEl.classList.remove("error");
    statusEl.textContent = "Finding your route...";
    resultEl.classList.remove("show");

    const requireStepFree = form.require_step_free.checked;
    const payload = {
      start_node_id: form.start_node_id.value,
      target_node_id: form.target_node_id.value,
      language: form.language.value,
      require_step_free: requireStepFree,
    };

    try {
      const response = await fetch("/api/wayfinding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Could not compute a route. Please try again.");
      }

      const data = await response.json();
      statusEl.textContent = `Route found: ${Math.round(data.route.total_walk_time_min)} min walk.`;

      titleEl.textContent = "Route Preview" + (requireStepFree ? " · Step-free" : "");
      distEl.textContent = `${(data.route.total_distance_m / 1000).toFixed(2)} km`;
      timeEl.textContent = `${Math.round(data.route.total_walk_time_min)} min`;
      stepsEl.innerHTML = data.route.steps
        .map((step, index) => `<li><span class="stepnum">${index + 1}</span><span>${step.node_name}</span></li>`)
        .join("");
      directionsEl.textContent = data.directions;
      resultEl.classList.add("show");
    } catch (err) {
      statusEl.classList.add("error");
      statusEl.textContent = err.message || "Something went wrong. Please try again.";
    }
  });
})();

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
      const data = await window.MatchDay.postJson(
        "/api/wayfinding",
        payload,
        "Could not compute a route. Please try again."
      );
      statusEl.textContent = `Route found: ${Math.round(data.route.total_walk_time_min)} min walk.`;

      titleEl.textContent = "Route Preview" + (requireStepFree ? " · Step-free" : "");
      distEl.textContent = `${(data.route.total_distance_m / 1000).toFixed(2)} km`;
      timeEl.textContent = `${Math.round(data.route.total_walk_time_min)} min`;

      // Build steps via DOM + textContent (not innerHTML) so node names are
      // never interpreted as markup.
      stepsEl.innerHTML = "";
      data.route.steps.forEach((step, index) => {
        const li = document.createElement("li");
        const num = document.createElement("span");
        num.className = "stepnum";
        num.textContent = String(index + 1);
        const name = document.createElement("span");
        name.textContent = step.node_name;
        li.append(num, name);
        stepsEl.appendChild(li);
      });
      directionsEl.textContent = data.directions;
      resultEl.classList.add("show");
    } catch (err) {
      statusEl.classList.add("error");
      statusEl.textContent = err.message || "Something went wrong. Please try again.";
    }
  });
})();

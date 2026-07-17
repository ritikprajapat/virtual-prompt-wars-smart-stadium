(function () {
  const form = document.getElementById("accessibility-form");
  const statusEl = document.getElementById("accessibility-status");
  const resultEl = document.getElementById("accessibility-result");
  const refEl = document.getElementById("accessibility-ref");
  const planEl = document.getElementById("accessibility-plan");
  const meetEl = document.getElementById("accessibility-meet");

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusEl.classList.remove("error");
    statusEl.textContent = "Drafting your accommodation plan...";
    resultEl.classList.remove("show");

    const payload = {
      need_type: form.need_type.value,
      target_node_id: form.target_node_id.value,
      language: form.language.value,
      notes: form.notes.value || null,
    };

    try {
      const data = await window.MatchDay.postJson(
        "/api/accessibility/request",
        payload,
        "Could not build a plan. Please try again."
      );
      statusEl.textContent = "Here is your accommodation plan:";

      refEl.textContent = "REF " + Math.random().toString(36).slice(2, 7).toUpperCase();
      planEl.textContent = data.plan;
      meetEl.textContent = data.facilities.length
        ? `Nearby accessible facilities: ${data.facilities.slice(0, 3).map((f) => f.name).join(", ")}.`
        : "";
      resultEl.classList.add("show");
    } catch (err) {
      statusEl.classList.add("error");
      statusEl.textContent = err.message || "Something went wrong. Please try again.";
    }
  });
})();

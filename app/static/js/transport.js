(function () {
  const form = document.getElementById("transport-form");
  const statusEl = document.getElementById("transport-status");
  const resultEl = document.getElementById("transport-result");
  const cardsEl = document.getElementById("transport-cards");

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusEl.classList.remove("error");
    statusEl.textContent = "Finding your best option...";
    resultEl.classList.remove("show");

    const payload = {
      distance_km: parseFloat(form.distance_km.value),
      language: "en",
    };

    try {
      const data = await window.MatchDay.postJson(
        "/api/transport/suggest",
        payload,
        "Could not fetch a suggestion. Please try again."
      );
      statusEl.textContent = "Suggestion ready:";

      cardsEl.innerHTML = `
        <div class="modecard best">
          <span class="mname">Best for you<span class="mtag">AI</span></span>
        </div>`;
      const note = document.createElement("p");
      note.className = "ai-note";
      note.textContent = data.suggestion;
      cardsEl.appendChild(note);
      resultEl.classList.add("show");
    } catch (err) {
      statusEl.classList.add("error");
      statusEl.textContent = err.message || "Something went wrong. Please try again.";
    }
  });
})();

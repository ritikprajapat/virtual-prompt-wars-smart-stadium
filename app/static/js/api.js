// Shared fetch helper for the fan-assistant forms. Centralises the POST +
// error-unwrapping pattern the four feature scripts previously duplicated, so
// each form handler only has to describe how to render its own result.
(function () {
  async function postJson(url, payload, fallbackMessage) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || fallbackMessage);
    }
    return response.json();
  }

  window.MatchDay = { postJson };
})();

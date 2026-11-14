/* SmartPick Hub AI search frontend.
   The API key stays on the backend; never add it to browser code. */
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("ai-search-form");
  if (!form) return;

  const input = document.getElementById("ai-search-input");
  const submit = document.getElementById("ai-search-submit");
  const result = document.getElementById("ai-search-result");
  const resultContent = document.getElementById("ai-search-result-content");
  const apiBase = String(window.SMARTPICK_API_BASE_URL || "").replace(/\/$/, "");

  document.querySelectorAll("[data-prompt]").forEach(function (button) {
    button.addEventListener("click", function () {
      input.value = button.dataset.prompt || "";
      input.focus();
    });
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    result.hidden = false;
    result.classList.remove("is-error");
    resultContent.textContent = "Thinking… Please wait while SmartPick AI prepares a response.";
    submit.disabled = true;
    submit.textContent = "Thinking…";

    if (!apiBase) {
      result.classList.add("is-error");
      resultContent.textContent = "SmartPick AI interface is ready, but its backend is not connected yet. The AI API must be configured on the secure server before live answers can be generated.";
      submit.disabled = false;
      submit.innerHTML = "<span aria-hidden=\"true\">✦</span> Ask AI";
      return;
    }

    try {
      const response = await fetch(apiBase + "/assistant/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query })
      });
      const data = await response.json().catch(function () { return {}; });
      if (!response.ok) {
        throw new Error(data.detail || "SmartPick AI could not answer right now.");
      }
      resultContent.textContent = data.answer || "No answer was returned. Please try again.";
    } catch (error) {
      result.classList.add("is-error");
      resultContent.textContent = error.message || "Connection error. Please try again later.";
    } finally {
      submit.disabled = false;
      submit.innerHTML = "<span aria-hidden=\"true\">✦</span> Ask AI";
    }
  });
});

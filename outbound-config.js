/* Optional FastAPI outbound-click endpoint. Keep blank until the backend is deployed. */
window.SMARTPICK_BACKEND_BASE_URL = "";

window.smartPickOutboundUrl = function (productId, fallbackUrl) {
  const base = String(window.SMARTPICK_BACKEND_BASE_URL || "").trim().replace(/\/$/, "");
  if (!base || !/^https:\/\//i.test(base) || !productId) return fallbackUrl;
  return base + "/out/" + encodeURIComponent(String(productId));
};

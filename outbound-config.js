/* Supabase Edge Function URL. Keep blank until the function is deployed and tested. */
window.SMARTPICK_OUTBOUND_FUNCTION_URL = "";

window.smartPickOutboundUrl = function (productId, fallbackUrl) {
  const endpoint = String(window.SMARTPICK_OUTBOUND_FUNCTION_URL || "").trim();
  if (!endpoint || !/^https:\/\//i.test(endpoint) || !productId) return fallbackUrl;
  const separator = endpoint.includes("?") ? "&" : "?";
  return endpoint + separator + "product_id=" + encodeURIComponent(String(productId));
};

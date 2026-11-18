/* Supabase Edge Function URL for tracked product redirects. */
window.SMARTPICK_OUTBOUND_FUNCTION_URL = "https://jimatgwmcasnbrhqhkbc.supabase.co/functions/v1/outbound-click";

window.smartPickOutboundUrl = function (productId, fallbackUrl) {
  const endpoint = String(window.SMARTPICK_OUTBOUND_FUNCTION_URL || "").trim();
  if (!endpoint || !/^https:\/\//i.test(endpoint) || !productId) return fallbackUrl;
  const separator = endpoint.includes("?") ? "&" : "?";
  return endpoint + separator + "product_id=" + encodeURIComponent(String(productId));
};

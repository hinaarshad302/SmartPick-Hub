import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? Deno.env.get("SUPABASE_SECRET_KEY") ?? "";
const CATALOGUE_URL = "https://hinaarshad302.github.io/SmartPick-Hub/products.json";
const ALLOWED_ORIGIN = "https://hinaarshad302.github.io";

const corsHeaders = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, apikey, x-client-info",
  "Cache-Control": "no-store",
  "Vary": "Origin",
};

function response(body: string, status: number) {
  return new Response(body, { status, headers: { ...corsHeaders, "Content-Type": "text/plain; charset=utf-8" } });
}

function safeHttpsDestination(value: unknown): string | null {
  if (typeof value !== "string" || value.length > 2048) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || !url.hostname || url.username || url.password) return null;
    return url.toString();
  } catch {
    return null;
  }
}

Deno.serve(async (request: Request) => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (request.method !== "GET") return response("Method not allowed.", 405);

  const productId = new URL(request.url).searchParams.get("product_id") ?? "";
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(productId) || productId.length > 120) {
    return response("Product not found.", 404);
  }
  if (!SUPABASE_URL || !SERVICE_ROLE_KEY) return response("Backend is not configured.", 503);

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  let product: Record<string, unknown> | null = null;
  let databaseLookupFailed = false;
  const { data, error } = await supabase
    .from("products")
    .select("id,status,affiliate_url,product_url")
    .eq("id", productId)
    .maybeSingle();

  if (error) {
    databaseLookupFailed = true;
  } else if (data) {
    if (data.status !== "published") return response("Product not found.", 404);
    product = data;
  }

  // The starter catalogue also lives in the public JSON file. This fixed-origin
  // fallback lets all curated products work before all 35 records are imported.
  if (!product && (!data || databaseLookupFailed)) {
    try {
      const catalogueResponse = await fetch(CATALOGUE_URL, { headers: { "Accept": "application/json" } });
      if (catalogueResponse.ok) {
        const catalogue = await catalogueResponse.json();
        if (Array.isArray(catalogue)) {
          product = catalogue.find((item) => item && item.id === productId && item.status === "published") ?? null;
        }
      }
    } catch {
      // Fail closed below; never accept a destination URL supplied by the visitor.
    }
  }

  if (!product) return response("Product not found.", 404);
  const affiliateUrl = String(product.affiliate_url ?? product.affiliateUrl ?? "");
  const retailerUrl = String(product.product_url ?? product.productUrl ?? "");
  const destination = safeHttpsDestination(affiliateUrl || retailerUrl);
  if (!destination) return response("Product destination is invalid.", 404);

  try {
    await supabase.from("affiliate_click_events").insert({
      product_id: productId,
      destination_type: affiliateUrl ? "affiliate" : "retailer",
    });
  } catch {
    // Analytics must never block a valid retailer redirect.
  }

  return new Response(null, {
    status: 302,
    headers: { ...corsHeaders, Location: destination },
  });
});

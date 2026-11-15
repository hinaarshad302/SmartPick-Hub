# Supabase Edge Function deployment

SmartPick Hub uses the existing Supabase project for the outbound product-click redirect. No Vercel backend is required for this feature.

## Files

- `functions/outbound-click/index.ts`: validates a published product, records a minimal click event, and redirects to its affiliate URL or retailer URL.
- `config.toml`: disables JWT verification for this public redirect endpoint. The function accepts only a product ID; it never accepts a destination URL from the browser.
- `../database/migrations/004_affiliate_click_events.sql`: creates the click-event table and grants INSERT only to the server role.

## One-time setup in the existing Supabase project

1. Open the Supabase project `jimatgwmcasnbrhqhkbc`.
2. In **SQL Editor**, run `database/migrations/004_affiliate_click_events.sql`. Confirm it completes successfully.
3. In the project terminal or a local terminal with the Supabase CLI installed, authenticate with `supabase login`.
4. From the repository root, link the existing project: `supabase link --project-ref jimatgwmcasnbrhqhkbc`.
5. Deploy the function: `supabase functions deploy outbound-click --no-verify-jwt`.
6. Test this endpoint in a browser: `https://jimatgwmcasnbrhqhkbc.supabase.co/functions/v1/outbound-click?product_id=logitech-c920s-webcam`. A valid published product should redirect to its HTTPS retailer page. A click row should appear in `affiliate_click_events`.

Supabase provides the function's project URL and service-role environment variable. If the project does not expose `SUPABASE_SERVICE_ROLE_KEY` automatically, set it as a function secret using the Supabase dashboard/CLI. Never put a service-role or secret key in website JavaScript, GitHub, or chat.

## Frontend

After the function is deployed and tested, `outbound-config.js` can point the product cards to the public function URL. It contains only the public project URL, not a secret. If the function is unavailable, the product card retains its direct retailer fallback.

## Privacy and limitations

The table stores only product ID, destination type, and timestamp. The function does not intentionally store visitor IP, user agent, referrer, or account ID. This is outbound click analytics only; it does not report orders, commission, or affiliate-network conversions. Real commission tracking requires approved affiliate URLs and conversion reporting from each affiliate network.

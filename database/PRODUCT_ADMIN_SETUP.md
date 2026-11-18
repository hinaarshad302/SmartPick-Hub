# SmartPick Hub Product Admin — Setup

This feature moves product records from the static `products.json` file into the Supabase `public.products` table. The public homepage, category pages, and Shop Products page read published products from that table. The private admin page writes product changes through the signed-in Supabase account.

## 1. Apply the database migration

1. Open the SmartPick Hub project in Supabase.
2. Open **SQL Editor** and create a new query.
3. Copy the complete contents of `database/migrations/003_product_catalog.sql`.
4. Run the query and confirm it finishes successfully.

The migration creates the catalogue and admin access table, enables Row Level Security, grants public read access only to published products, restricts catalogue writes to approved administrators, and imports the five existing Technology starter picks.

## 2. Grant your own account admin access

1. Sign up for a normal SmartPick Hub account using the email address you will use as the site owner.
2. Confirm the email and sign in once.
3. In Supabase **SQL Editor**, run the following query after replacing the email with your own login email:

```sql
insert into public.smartpick_admins (user_id)
select id
from auth.users
where lower(email) = lower('YOUR-LOGIN-EMAIL')
on conflict (user_id) do nothing;
```

4. If the query inserts zero rows, check that the account exists in Supabase Auth and that the email matches exactly.
5. Never add an administrator by changing browser-side user metadata. Only a trusted project owner should run this SQL.

## 3. Open the admin page

Visit:

`https://hinaarshad302.github.io/SmartPick-Hub/products-admin.html`

Sign in with the approved account. The admin page checks the `smartpick_admins` table before showing catalogue controls.

## 4. Add or update a product

- Enter a unique URL-safe Product ID, for example `anker-power-bank-20k`.
- Select the matching department. It determines which category page displays the product.
- Add a product name, category, description, and market(s).
- Use HTTPS for image and destination URLs.
- Use the affiliate URL only after approval by that affiliate programme. If there is no approved affiliate URL, use the normal retailer/manufacturer URL; the public button will be labelled as a manufacturer/retailer link.
- Keep the product as **Draft** until details and links have been checked. Set it to **Published** when ready.

The homepage shows all published products. A category page shows only published products assigned to its department. Shop Products shows all published products with search and filters.

## Security notes

- The browser uses only the Supabase publishable key already configured for the site.
- Do not put a service-role/secret key, GitHub personal access token, or Gemini API key in HTML or JavaScript.
- RLS protects product writes even if someone opens the admin page URL.
- The admin page URL is not a security boundary; database policies are.
- Before launch, test with two accounts: an approved admin and a normal customer. The customer must not be able to insert, update, or delete catalogue records.
- GitHub Pages deployment is separate from committing these files. Check the configured Pages deployment before assuming the live site has updated.

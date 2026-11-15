-- SmartPick Hub central product catalogue and admin access.
-- Apply this migration in the Supabase SQL Editor.
-- Then add your own account to smartpick_admins using the SQL at the end of this file.
-- Never expose a Supabase service-role/secret key in browser code.

begin;

create table if not exists public.smartpick_admins (
    user_id uuid primary key references auth.users(id) on delete cascade,
    created_at timestamptz not null default now()
);

alter table public.smartpick_admins enable row level security;
revoke all on table public.smartpick_admins from public, anon, authenticated;
grant select on table public.smartpick_admins to anon, authenticated;

drop policy if exists "Admins can read their own admin record" on public.smartpick_admins;
create policy "Admins can read their own admin record"
    on public.smartpick_admins for select to authenticated
    using ((select auth.uid()) = user_id);

create table if not exists public.products (
    id text primary key check (id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    name text not null check (char_length(trim(name)) between 2 and 180),
    category text not null check (char_length(trim(category)) between 2 and 80),
    department text not null check (department in (
        'Technology', 'Electronics & Gadgets', 'Kitchen & Home',
        'Beauty', 'Fashion', 'Health & Fitness', 'Daily Use'
    )),
    markets text[] not null default '{}',
    description text not null default '',
    image text not null default '',
    price text not null default '',
    merchant text not null default '',
    affiliate_url text not null default '',
    product_url text not null default '',
    status text not null default 'draft' check (status in ('draft', 'published', 'archived')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint products_link_required check (
        affiliate_url = '' or affiliate_url ~ '^https://'
    ),
    constraint products_product_link_https check (
        product_url = '' or product_url ~ '^https://'
    ),
    constraint products_image_https check (
        image = '' or image ~ '^https://'
    ),
    constraint products_destination_required check (
        affiliate_url <> '' or product_url <> ''
    )
);

create index if not exists products_status_department_idx
    on public.products(status, department);
create index if not exists products_category_idx on public.products(category);

alter table public.products enable row level security;
revoke all on table public.products from public, anon, authenticated;
grant select on table public.products to anon, authenticated;
grant insert, update, delete on table public.products to authenticated;

drop policy if exists "Anyone can read published products" on public.products;
create policy "Anyone can read published products"
    on public.products for select to anon, authenticated
    using (
        status = 'published'
        or exists (
            select 1 from public.smartpick_admins a
            where a.user_id = (select auth.uid())
        )
    );

drop policy if exists "Admins can insert products" on public.products;
create policy "Admins can insert products"
    on public.products for insert to authenticated
    with check (
        exists (
            select 1 from public.smartpick_admins a
            where a.user_id = (select auth.uid())
        )
    );

drop policy if exists "Admins can update products" on public.products;
create policy "Admins can update products"
    on public.products for update to authenticated
    using (
        exists (
            select 1 from public.smartpick_admins a
            where a.user_id = (select auth.uid())
        )
    )
    with check (
        exists (
            select 1 from public.smartpick_admins a
            where a.user_id = (select auth.uid())
        )
    );

drop policy if exists "Admins can delete products" on public.products;
create policy "Admins can delete products"
    on public.products for delete to authenticated
    using (
        exists (
            select 1 from public.smartpick_admins a
            where a.user_id = (select auth.uid())
        )
    );

create or replace function public.set_products_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog
as $$
begin
    new.updated_at = pg_catalog.now();
    return new;
end;
$$;

revoke all on function public.set_products_updated_at() from public, anon, authenticated;
drop trigger if exists products_set_updated_at on public.products;
create trigger products_set_updated_at
    before update on public.products
    for each row execute function public.set_products_updated_at();

-- Import the five existing starter products. Their links remain manufacturer links,
-- not affiliate links. Re-running this migration safely updates the same product IDs.
insert into public.products
(id, name, category, department, markets, description, image, merchant, product_url, status)
values
('logitech-c920s-webcam', 'Logitech C920s Pro HD Webcam', 'Webcams', 'Technology', array['USA'],
 'A Full HD 1080p webcam with autofocus, automatic light correction, dual stereo microphones and a privacy shutter. A practical option for online classes and video meetings.',
 'https://resource.logitech.com/w_544%2Ch_466%2Car_7%3A6%2Cc_pad%2Cq_auto%2Cf_auto%2Cdpr_1.0/d_transparent.gif/content/dam/logitech/en/products/webcams/c920s/gallery/c920s-gallery-1.png',
 'Logitech', 'https://www.logitech.com/en-us/shop/p/c920s-pro-hd-webcam.960-001252', 'published'),
('dell-pro-3-webcam-2k', 'Dell Pro 3 Webcam 2K (WB3023)', 'Webcams', 'Technology', array['USA'],
 'A 2K QHD webcam supporting up to 2560 × 1440 resolution at 60 fps, with a 78° field of view, autofocus and built-in microphone. Check device and software compatibility before buying.',
 'https://i.dell.com/sites/csimages/Video_Imagery/all/dell-webcam-wb3023-thumbnail.jpg',
 'Dell', 'https://www.dell.com/en-us/shop/clientaudiovideo/apd/dell-pro-3-webcam-2k-wb3023/dp1x1/-', 'published'),
('logitech-mx-keys-s', 'Logitech MX Keys S Wireless Keyboard', 'Keyboards', 'Technology', array['USA'],
 'A low-profile wireless keyboard with smart backlighting, programmable keys and multi-device switching. Designed for comfortable, precise typing at a desk.',
 'https://resource.logitech.com/w_544%2Ch_466%2Car_7%3A6%2Cc_pad%2Cq_auto%2Cf_auto%2Cdpr_1.0/d_transparent.gif/content/dam/logitech/en/products/keyboards/mx-keys-s/migration-assets-for-delorean-2025/gallery/mx-keys-s-top-view-black-us.png',
 'Logitech', 'https://www.logitech.com/en-us/shop/p/mx-keys-s', 'published'),
('anker-usb-c-hub-7-in-1', 'Anker USB-C Hub (7-in-1)', 'Connectivity', 'Technology', array['USA'],
 'A compact USB-C hub that adds multiple connections, including HDMI, USB and card access. The manufacturer lists 4K at 60Hz HDMI output and up to 85W charging; verify your laptop USB-C capabilities.',
 'https://cdn.shopify.com/s/files/1/0493/9834/9974/files/image_11_3f856f3b-1d0b-4609-974f-af0ea4ca2d12.png?v=1764833041&width=3840',
 'Anker', 'https://www.anker.com/products/a83d2-usb-c-hub-7-in-1', 'published'),
('samsung-t7-shield-1tb', 'Samsung T7 Shield Portable SSD (1TB)', 'Storage', 'Technology', array['USA'],
 'A rugged 1TB portable SSD with USB 3.2 Gen 2, IP65-rated protection and advertised sequential read/write speeds of up to 1,050/1,000 MB/s. Actual speeds depend on the connected device and setup.',
 'https://images.samsung.com/is/image/samsung/p6pim/us/mu-pe1t0s-am/gallery/us-portable-ssd-t7-shield-mu-pe1t0s-am-552408700?$product-details-jpg$=',
 'Samsung', 'https://www.samsung.com/us/memory-storage/portable-ssd/portable-ssd-t7-shield-usb-3-2-1tb-black-sku-mu-pe1t0s-am/', 'published')
on conflict (id) do update set
 name = excluded.name, category = excluded.category, department = excluded.department,
 markets = excluded.markets, description = excluded.description, image = excluded.image,
 merchant = excluded.merchant, product_url = excluded.product_url, status = excluded.status;

commit;

-- AFTER running the migration and confirming your account exists in Supabase Auth,
-- replace the email below with the email you use to sign in, then run this separately:
-- insert into public.smartpick_admins (user_id)
-- select id from auth.users where lower(email) = lower('YOUR-LOGIN-EMAIL')
-- on conflict (user_id) do nothing;

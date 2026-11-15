-- Privacy-conscious outbound product click events.
-- Apply after 003_product_catalog.sql. Browser roles receive no access;
-- only the server-side FastAPI service-role client writes events.

begin;

create table if not exists public.affiliate_click_events (
    id uuid primary key default gen_random_uuid(),
    product_id text not null check (char_length(trim(product_id)) between 1 and 120),
    destination_type text not null check (destination_type in ('affiliate', 'retailer')),
    clicked_at timestamptz not null default now()
);

create index if not exists affiliate_click_events_clicked_at_idx
    on public.affiliate_click_events (clicked_at desc);
create index if not exists affiliate_click_events_product_id_idx
    on public.affiliate_click_events (product_id, clicked_at desc);

alter table public.affiliate_click_events enable row level security;
revoke all on table public.affiliate_click_events from public, anon, authenticated;
grant insert on table public.affiliate_click_events to service_role;

comment on table public.affiliate_click_events is
    'Minimal outbound product click analytics. Stores product ID, destination type, and timestamp only; no visitor identifiers.';

commit;

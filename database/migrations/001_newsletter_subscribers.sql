-- SmartPick Hub newsletter subscribers
-- Apply this migration in the Supabase SQL Editor or through Supabase CLI.
-- The backend accesses this table with a server-side Supabase secret key.
-- Public browser roles must not read or modify subscriber records.

create table if not exists public.newsletter_subscribers (
    id uuid primary key default gen_random_uuid(),
    email text not null,
    status text not null default 'pending'
        check (status in ('pending', 'confirmed', 'unsubscribed')),
    confirmation_token_hash text,
    confirmation_expires_at timestamptz,
    unsubscribe_token_hash text,
    confirmed_at timestamptz,
    unsubscribed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint newsletter_subscribers_email_lowercase
        check (email = lower(trim(email)))
);

create unique index if not exists newsletter_subscribers_email_uidx
    on public.newsletter_subscribers (email);

create unique index if not exists newsletter_subscribers_confirmation_token_uidx
    on public.newsletter_subscribers (confirmation_token_hash)
    where confirmation_token_hash is not null;

create unique index if not exists newsletter_subscribers_unsubscribe_token_uidx
    on public.newsletter_subscribers (unsubscribe_token_hash)
    where unsubscribe_token_hash is not null;

create index if not exists newsletter_subscribers_status_idx
    on public.newsletter_subscribers (status);

alter table public.newsletter_subscribers enable row level security;

-- No browser access to subscriber emails or one-time token hashes.
revoke all on table public.newsletter_subscribers from anon, authenticated;
grant all on table public.newsletter_subscribers to service_role;

comment on table public.newsletter_subscribers is
    'Private newsletter subscription records. Access is server-side only.';

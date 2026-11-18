-- SmartPick Hub private user profile records.
-- Each authenticated user may read and update only their own profile row.
-- This table is not used by the current frontend until this migration is applied.

begin;

create table public.user_profiles (
    user_id uuid primary key references auth.users (id) on delete cascade,
    display_name text not null
        check (char_length(trim(display_name)) between 2 and 60),
    created_at timestamptz not null default pg_catalog.now(),
    updated_at timestamptz not null default pg_catalog.now()
);

alter table public.user_profiles enable row level security;

revoke all on table public.user_profiles from public, anon, authenticated;
grant select, insert, update on table public.user_profiles to authenticated;

create policy "Users can read their own profile"
    on public.user_profiles
    for select
    to authenticated
    using ((select auth.uid()) = user_id);

create policy "Users can create their own profile"
    on public.user_profiles
    for insert
    to authenticated
    with check ((select auth.uid()) = user_id);

create policy "Users can update their own profile"
    on public.user_profiles
    for update
    to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

create function public.set_user_profiles_updated_at()
returns trigger
language plpgsql
set search_path = pg_catalog
as $$
begin
    new.updated_at = pg_catalog.now();
    return new;
end;
$$;

revoke all on function public.set_user_profiles_updated_at() from public, anon, authenticated;

create trigger user_profiles_set_updated_at
    before update on public.user_profiles
    for each row
    execute function public.set_user_profiles_updated_at();

comment on table public.user_profiles is
    'Private per-user profile fields. RLS restricts rows to auth.uid().';

commit;

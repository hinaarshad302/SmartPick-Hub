-- Run after applying 004_affiliate_click_events.sql in the Supabase SQL Editor.
-- Verifies that click analytics remain private to the server-side backend.

do $$
begin
    if not exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'affiliate_click_events'
          and c.relrowsecurity = true
    ) then
        raise exception 'RLS is not enabled on public.affiliate_click_events';
    end if;

    if has_table_privilege('anon', 'public.affiliate_click_events', 'SELECT')
       or has_table_privilege('anon', 'public.affiliate_click_events', 'INSERT')
       or has_table_privilege('anon', 'public.affiliate_click_events', 'UPDATE')
       or has_table_privilege('anon', 'public.affiliate_click_events', 'DELETE') then
        raise exception 'anon role must not access affiliate click events';
    end if;

    if has_table_privilege('authenticated', 'public.affiliate_click_events', 'SELECT')
       or has_table_privilege('authenticated', 'public.affiliate_click_events', 'INSERT')
       or has_table_privilege('authenticated', 'public.affiliate_click_events', 'UPDATE')
       or has_table_privilege('authenticated', 'public.affiliate_click_events', 'DELETE') then
        raise exception 'authenticated browser role must not access affiliate click events';
    end if;

    if not has_table_privilege('service_role', 'public.affiliate_click_events', 'INSERT') then
        raise exception 'service_role must be able to insert click events';
    end if;

    if has_table_privilege('anon', 'public.affiliate_click_events', 'TRUNCATE')
       or has_table_privilege('authenticated', 'public.affiliate_click_events', 'TRUNCATE') then
        raise exception 'Browser roles must not truncate affiliate click events';
    end if;
end;
$$;

-- Run after applying 001_newsletter_subscribers.sql in the Supabase SQL Editor.
-- These checks confirm the browser roles cannot access subscriber data.

do $$
begin
    if not exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'newsletter_subscribers'
          and c.relrowsecurity = true
    ) then
        raise exception 'RLS is not enabled on newsletter_subscribers';
    end if;

    if has_table_privilege('anon', 'public.newsletter_subscribers', 'SELECT')
       or has_table_privilege('anon', 'public.newsletter_subscribers', 'INSERT')
       or has_table_privilege('anon', 'public.newsletter_subscribers', 'UPDATE')
       or has_table_privilege('anon', 'public.newsletter_subscribers', 'DELETE') then
        raise exception 'anon role has an unexpected privilege on newsletter_subscribers';
    end if;

    if has_table_privilege('authenticated', 'public.newsletter_subscribers', 'SELECT')
       or has_table_privilege('authenticated', 'public.newsletter_subscribers', 'INSERT')
       or has_table_privilege('authenticated', 'public.newsletter_subscribers', 'UPDATE')
       or has_table_privilege('authenticated', 'public.newsletter_subscribers', 'DELETE') then
        raise exception 'authenticated role has an unexpected privilege on newsletter_subscribers';
    end if;

    if not has_table_privilege('service_role', 'public.newsletter_subscribers', 'SELECT')
       or not has_table_privilege('service_role', 'public.newsletter_subscribers', 'INSERT')
       or not has_table_privilege('service_role', 'public.newsletter_subscribers', 'UPDATE') then
        raise exception 'service_role is missing a required backend privilege';
    end if;
end;
$$;

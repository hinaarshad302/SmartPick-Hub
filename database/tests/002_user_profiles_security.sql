-- Run after applying 002_user_profiles.sql in Supabase SQL Editor.
-- Checks RLS, least-privilege grants, and the three owner-scoped policies.

do $$
declare
    policy_count integer;
begin
    if not exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'user_profiles'
          and c.relrowsecurity = true
    ) then
        raise exception 'RLS is not enabled on user_profiles';
    end if;

    if has_table_privilege('anon', 'public.user_profiles', 'SELECT')
       or has_table_privilege('anon', 'public.user_profiles', 'INSERT')
       or has_table_privilege('anon', 'public.user_profiles', 'UPDATE')
       or has_table_privilege('anon', 'public.user_profiles', 'DELETE') then
        raise exception 'anon role has an unexpected privilege on user_profiles';
    end if;

    if has_table_privilege('authenticated', 'public.user_profiles', 'DELETE')
       or has_table_privilege('authenticated', 'public.user_profiles', 'TRUNCATE')
       or has_table_privilege('authenticated', 'public.user_profiles', 'REFERENCES')
       or has_table_privilege('authenticated', 'public.user_profiles', 'TRIGGER') then
        raise exception 'authenticated role has an unexpected elevated privilege on user_profiles';
    end if;

    if not has_table_privilege('authenticated', 'public.user_profiles', 'SELECT')
       or not has_table_privilege('authenticated', 'public.user_profiles', 'INSERT')
       or not has_table_privilege('authenticated', 'public.user_profiles', 'UPDATE') then
        raise exception 'authenticated role is missing a required profile privilege';
    end if;

    select count(*) into policy_count
    from pg_policies
    where schemaname = 'public'
      and tablename = 'user_profiles'
      and policyname in (
          'Users can read their own profile',
          'Users can create their own profile',
          'Users can update their own profile'
      );

    if policy_count <> 3 then
        raise exception 'Expected three owner-scoped user_profiles policies, found %', policy_count;
    end if;

    if exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'user_profiles'
          and (
              coalesce(qual, '') not like '%auth.uid()%'
              or (
                  cmd in ('INSERT', 'ALL')
                  and coalesce(with_check, '') not like '%auth.uid()%'
              )
          )
          and policyname in (
              'Users can read their own profile',
              'Users can create their own profile',
              'Users can update their own profile'
          )
    ) then
        raise exception 'A user_profiles policy is missing an auth.uid() ownership condition';
    end if;
end;
$$;

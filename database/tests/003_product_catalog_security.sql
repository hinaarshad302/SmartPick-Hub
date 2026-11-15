-- Run after applying 003_product_catalog.sql in the Supabase SQL Editor.
-- Verifies that public visitors can only read published products and that
-- product mutations/admin membership remain protected by Supabase RLS.

do $$
declare
    product_policy_count integer;
begin
    if not exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'products'
          and c.relrowsecurity = true
    ) then
        raise exception 'RLS is not enabled on public.products';
    end if;

    if not exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'smartpick_admins'
          and c.relrowsecurity = true
    ) then
        raise exception 'RLS is not enabled on public.smartpick_admins';
    end if;

    if not has_table_privilege('anon', 'public.products', 'SELECT') then
        raise exception 'anon role must be able to read published products';
    end if;

    if has_table_privilege('anon', 'public.products', 'INSERT')
       or has_table_privilege('anon', 'public.products', 'UPDATE')
       or has_table_privilege('anon', 'public.products', 'DELETE') then
        raise exception 'anon role has an unexpected write privilege on products';
    end if;

    if not has_table_privilege('authenticated', 'public.products', 'SELECT')
       or not has_table_privilege('authenticated', 'public.products', 'INSERT')
       or not has_table_privilege('authenticated', 'public.products', 'UPDATE')
       or not has_table_privilege('authenticated', 'public.products', 'DELETE') then
        raise exception 'authenticated role is missing a product privilege required by the admin policies';
    end if;

    if has_table_privilege('anon', 'public.smartpick_admins', 'INSERT')
       or has_table_privilege('anon', 'public.smartpick_admins', 'UPDATE')
       or has_table_privilege('anon', 'public.smartpick_admins', 'DELETE')
       or has_table_privilege('authenticated', 'public.smartpick_admins', 'INSERT')
       or has_table_privilege('authenticated', 'public.smartpick_admins', 'UPDATE')
       or has_table_privilege('authenticated', 'public.smartpick_admins', 'DELETE') then
        raise exception 'Browser roles must not be able to modify smartpick_admins';
    end if;

    select count(*) into product_policy_count
    from pg_policies
    where schemaname = 'public'
      and tablename = 'products'
      and policyname in (
          'Anyone can read published products',
          'Admins can insert products',
          'Admins can update products',
          'Admins can delete products'
      );

    if product_policy_count <> 4 then
        raise exception 'Expected four product policies, found %', product_policy_count;
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'public'
          and tablename = 'products'
          and policyname = 'Anyone can read published products'
          and cmd = 'SELECT'
          and coalesce(qual, '') like '%status = ''published''%'
          and coalesce(qual, '') like '%smartpick_admins%'
    ) then
        raise exception 'Published-product read policy is missing its published/admin conditions';
    end if;

    if exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'products'
          and policyname in (
              'Admins can insert products',
              'Admins can update products',
              'Admins can delete products'
          )
          and (
              coalesce(qual, '') not like '%smartpick_admins%'
              or (cmd in ('INSERT', 'UPDATE')
                  and coalesce(with_check, '') not like '%smartpick_admins%')
          )
    ) then
        raise exception 'A product mutation policy is missing its admin-membership condition';
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'smartpick_admins'
          and policyname = 'Admins can read their own admin record'
          and cmd = 'SELECT'
          and coalesce(qual, '') like '%auth.uid()%'
    ) then
        raise exception 'Admin membership read policy is missing its user-ownership condition';
    end if;
end;
$$;

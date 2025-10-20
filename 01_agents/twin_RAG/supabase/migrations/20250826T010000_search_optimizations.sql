-- Enable pg_trgm for better ILIKE performance and create GIN indexes
create extension if not exists pg_trgm;

-- Create indexes only if table exists (avoid errors when base table not yet created)
do $$
begin
  if exists (
    select 1
    from information_schema.tables
    where table_schema = 'public' and table_name = 'places'
  ) then
    create index if not exists places_name_ko_trgm_idx on public.places using gin (name_ko gin_trgm_ops);
    create index if not exists places_name_en_trgm_idx on public.places using gin (name_en gin_trgm_ops);
    create index if not exists places_address_ko_trgm_idx on public.places using gin (address_ko gin_trgm_ops);
    create index if not exists places_address_en_trgm_idx on public.places using gin (address_en gin_trgm_ops);
    create index if not exists places_phone_trgm_idx on public.places using gin (phone gin_trgm_ops);
  end if;
end $$;



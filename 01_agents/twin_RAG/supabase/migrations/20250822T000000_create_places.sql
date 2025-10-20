-- Places table for sample datasets
create table if not exists public.places (
  id uuid primary key,
  name_ko text not null,
  name_en text,
  category text not null check (category in ('HOSPITAL','BANK','EVENT','SCHOOL','GOVERNMENT','OTHER')),
  latitude double precision,
  longitude double precision,
  address_ko text,
  address_en text,
  phone text,
  opening_hours jsonb,
  source_url text,
  source_name text,
  verified_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists places_category_idx on public.places(category);
create index if not exists places_geo_idx on public.places(latitude, longitude);



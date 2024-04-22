create table
  public.potions (
    "SKU" text not null,
    name text null,
    red integer null,
    green integer null,
    blue integer null,
    dark integer null,
    quantity integer null,
    price integer null,
    constraint potions_pkey primary key ("SKU"),
    constraint potions_SKU_key unique ("SKU")
  ) tablespace pg_default;
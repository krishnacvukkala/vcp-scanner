-- Aaroquant VCP Scanner — Supabase schema
--
-- Paste this whole file into the Supabase SQL Editor and press Run. It is
-- idempotent: running it twice is harmless.
--
-- What lives here and why:
--   scan_runs           one row per completed scan (the funnel counts, timing,
--                       and which settings produced it)
--   scan_results        one row per symbol per run, with the full strategy
--                       record kept verbatim as JSON so the dashboard can
--                       render exactly what the engine decided
--   ohlcv_cache         chart series, so opening a chart does not hit Yahoo
--   fundamentals_cache  quarterly statements and ratios, refreshed daily
--
-- Security model: row-level security is ON with no policies, so the public
-- anon key can read nothing. Only the service-role key (used server-side by
-- the Flask API and the scheduled scanner) can touch these tables. Never put
-- the service-role key in the browser.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Scan runs
-- ---------------------------------------------------------------------------
create table if not exists public.scan_runs (
    id                  uuid primary key default gen_random_uuid(),
    started_at          timestamptz not null,
    finished_at         timestamptz,
    status              text        not null default 'running',
                        -- 'running' | 'complete' | 'failed'
    source              text,       -- 'github-actions' | 'local' | 'manual'
    universe_size       integer,
    scanned             integer,
    elapsed_seconds     numeric,
    hidden_by_prescreen integer     not null default 0,
    counts              jsonb       not null default '{}'::jsonb,
    settings            jsonb       not null default '{}'::jsonb,
    user_parameters     jsonb       not null default '[]'::jsonb,
    caveats             jsonb       not null default '[]'::jsonb,
    failures            jsonb       not null default '[]'::jsonb,
    error               text,
    created_at          timestamptz not null default now()
);

create index if not exists scan_runs_recent_idx
    on public.scan_runs (status, started_at desc);

-- ---------------------------------------------------------------------------
-- Scan results
-- ---------------------------------------------------------------------------
-- The promoted columns exist so the dashboard can filter and sort in SQL.
-- `record` is the untouched engine output — it is the source of truth, and
-- the columns are derived from it, never the other way round.
create table if not exists public.scan_results (
    run_id                uuid not null
                          references public.scan_runs(id) on delete cascade,
    symbol                text not null,
    name                  text,
    exchange              text,
    country               text,
    asset_class           text,
    currency              text,
    verdict               text,
    status                text,
    as_of                 date,
    close                 numeric,
    contractions          integer,
    distance_to_pivot_pct numeric,
    risk_pct              numeric,
    pivot                 numeric,
    stop                  numeric,
    record                jsonb not null,
    primary key (run_id, symbol)
);

create index if not exists scan_results_run_verdict_idx
    on public.scan_results (run_id, verdict);
create index if not exists scan_results_symbol_idx
    on public.scan_results (symbol);
create index if not exists scan_results_country_idx
    on public.scan_results (run_id, country);

-- ---------------------------------------------------------------------------
-- Caches
-- ---------------------------------------------------------------------------
-- Keyed by (symbol, timeframe): the dashboard's chart asks for 1D/1W/1h and
-- each is a different series. `payload` is exactly what /api/market-data/ohlc
-- returns, so a cache hit and a live fetch are byte-identical to the chart.
create table if not exists public.ohlcv_cache (
    symbol          text not null,
    timeframe       text not null default '1D',
    provider_symbol text,
    exchange        text,
    candles         integer,
    payload         jsonb       not null,
    updated_at      timestamptz not null default now(),
    primary key (symbol, timeframe)
);

create table if not exists public.fundamentals_cache (
    symbol     text primary key,
    exchange   text,
    payload    jsonb       not null,
    updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Convenience view: the most recent completed run
-- ---------------------------------------------------------------------------
create or replace view public.latest_scan_run as
    select *
      from public.scan_runs
     where status = 'complete'
     order by started_at desc
     limit 1;

-- ---------------------------------------------------------------------------
-- Row-level security: deny by default
-- ---------------------------------------------------------------------------
-- No policies are created, so anon and authenticated roles get nothing. The
-- service-role key bypasses RLS entirely, which is how the server reads and
-- writes. If you later want the browser to read directly, add explicit
-- select policies here rather than loosening these.
alter table public.scan_runs          enable row level security;
alter table public.scan_results       enable row level security;
alter table public.ohlcv_cache        enable row level security;
alter table public.fundamentals_cache enable row level security;

-- ---------------------------------------------------------------------------
-- Retention helper (optional)
-- ---------------------------------------------------------------------------
-- Keeps the newest 60 completed runs and deletes the rest. scan_results rows
-- go with them via the cascade. Run it by hand, or from the scheduled job.
create or replace function public.prune_scan_history(keep integer default 60)
returns integer
language plpgsql
as $$
declare
    removed integer;
begin
    with doomed as (
        select id from public.scan_runs
        order by started_at desc
        offset keep
    )
    delete from public.scan_runs r using doomed d where r.id = d.id;
    get diagnostics removed = row_count;
    return removed;
end;
$$;

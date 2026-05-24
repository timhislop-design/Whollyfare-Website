-- =============================================================================
-- WhollyFare® — Migration 002: Platform Flyer Tables
-- Sentir Solutions® LLC · Charlottesville, VA
-- May 2026
--
-- WHY THIS EXISTS:
--   The original flyer_weeks + flyer_items tables are per-household (tied to
--   household_id). This worked when each household uploaded their own circulars,
--   but WhollyFare's model is now operator-run: Tim uploads store flyers once
--   per week and every authenticated user sees the same platform-level prices.
--
--   These two new tables decouple flyer data from households entirely.
--   Tim writes as service_role (bypasses RLS). Any authenticated user reads.
--
-- HOW TO RUN:
--   Supabase Dashboard → SQL Editor → paste + run.
--   Or: Supabase MCP apply_migration.
--
-- WHAT THIS CREATES:
--   platform_flyer_weeks  — one row per (chain, week). Upserted each upload.
--   platform_flyer_items  — one row per sale item. Deleted + re-inserted
--                           each upload so stale items never persist.
--
-- RELATIONSHIP TO OLD TABLES:
--   flyer_weeks / flyer_items remain in the schema (not dropped) but are
--   no longer written to by the app. They can be dropped in Migration 003
--   after confirming no active data depends on them.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- platform_flyer_weeks
-- One row per (chain_name, week_start_date). Upserted on each Admin upload.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.platform_flyer_weeks (
    id               uuid        DEFAULT uuid_generate_v4() PRIMARY KEY,
    chain_name       text        NOT NULL,
    week_start_date  date        NOT NULL,
    load_method      text        NOT NULL DEFAULT 'pdf'
                         CHECK (load_method IN ('manual', 'pdf', 'api')),
    item_count       int         NOT NULL DEFAULT 0,
    loaded_by        uuid        REFERENCES auth.users(id) ON DELETE SET NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (chain_name, week_start_date)
);

CREATE INDEX IF NOT EXISTS platform_flyer_weeks_chain_week
    ON public.platform_flyer_weeks (chain_name, week_start_date DESC);

-- RLS: authenticated users can read; service_role writes (bypasses RLS)
ALTER TABLE public.platform_flyer_weeks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "authenticated users can read platform flyer weeks"
    ON public.platform_flyer_weeks
    FOR SELECT
    TO authenticated
    USING (true);


-- ---------------------------------------------------------------------------
-- platform_flyer_items
-- One row per sale item. Deleted + re-inserted each week to avoid stale data.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.platform_flyer_items (
    id                uuid        DEFAULT uuid_generate_v4() PRIMARY KEY,
    platform_week_id  uuid        NOT NULL
                         REFERENCES public.platform_flyer_weeks(id) ON DELETE CASCADE,
    chain_name        text        NOT NULL,   -- denormalized for fast chain-filtered queries
    name              text        NOT NULL,
    category          text        NOT NULL DEFAULT 'other',
    unit              text        NOT NULL DEFAULT 'each',
    sale_price        numeric(8,2),
    regular_price     numeric(8,2),
    allergens         text[]      NOT NULL DEFAULT '{}',
    tags              text[]      NOT NULL DEFAULT '{}',
    usda_fdc_id       text,
    is_manual         boolean     NOT NULL DEFAULT false,
    created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS platform_flyer_items_by_week
    ON public.platform_flyer_items (platform_week_id);

CREATE INDEX IF NOT EXISTS platform_flyer_items_by_chain
    ON public.platform_flyer_items (chain_name);

CREATE INDEX IF NOT EXISTS platform_flyer_items_chain_week
    ON public.platform_flyer_items (chain_name, platform_week_id);

-- RLS: authenticated users can read; service_role writes (bypasses RLS)
ALTER TABLE public.platform_flyer_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "authenticated users can read platform flyer items"
    ON public.platform_flyer_items
    FOR SELECT
    TO authenticated
    USING (true);


-- ---------------------------------------------------------------------------
-- Notes for future migrations
-- ---------------------------------------------------------------------------
-- Migration 003 (when ready): DROP TABLE public.flyer_items, public.flyer_weeks
--   (only after confirming no production data depends on them)
--
-- Phase 3 additions to platform_flyer_items:
--   - normalized_name text  (for price history joins)
--   - price_per_oz numeric  (unit-normalized comparison)
--   - source_page int       (which PDF page the item came from)
-- =============================================================================

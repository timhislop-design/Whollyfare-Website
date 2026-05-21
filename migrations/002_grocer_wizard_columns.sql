-- ─────────────────────────────────────────────────────────────────────────────
-- Migration 002 — Grocer wizard persistence columns
-- Run once against the WhollyFare Supabase project.
--
-- Adds the fields the Grocer Hub wizard collects that were missing from
-- the Phase 1 schema: tier, lat/lon, distance, travel radius preference.
--
-- Safe to re-run: all statements use IF NOT EXISTS / DO NOTHING patterns.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 1. household_grocers — new columns ───────────────────────────────────────
-- tier:           which bucket the store falls into (discount/mainstream/
--                 specialty/local) — drives UI grouping and cost logic
-- distance_miles: one-way miles from the household zip to this store
--                 (Haversine; overrideable by user)
-- lat / lon:      store coordinates from store_locations.py registry
--                 (NULL when store is outside the pilot area hardcoded list)
--                 PROD: populated from Google Places API

ALTER TABLE household_grocers
    ADD COLUMN IF NOT EXISTS tier            TEXT,
    ADD COLUMN IF NOT EXISTS distance_miles  NUMERIC(6, 2),
    ADD COLUMN IF NOT EXISTS lat             NUMERIC(10, 7),
    ADD COLUMN IF NOT EXISTS lon             NUMERIC(10, 7);

-- ── 2. households — travel radius preference ─────────────────────────────────
-- travel_radius_mi: how far the household is willing to travel to shop.
-- Set in the Grocer Hub wizard; used to filter which stores are surfaced.
-- Default 15 miles matches the app default in state.py.

ALTER TABLE households
    ADD COLUMN IF NOT EXISTS travel_radius_mi  SMALLINT DEFAULT 15;

-- ── 3. household_grocers — upsert conflict target ────────────────────────────
-- The save_grocers() Python function does an upsert on
-- (household_id, chain_name). We need a unique constraint for
-- ON CONFLICT ... DO UPDATE to work cleanly.
-- IF the constraint already exists this is a no-op.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'household_grocers_household_chain_unique'
    ) THEN
        ALTER TABLE household_grocers
            ADD CONSTRAINT household_grocers_household_chain_unique
            UNIQUE (household_id, chain_name);
    END IF;
END $$;

-- ── Done ──────────────────────────────────────────────────────────────────────
-- After running this migration:
--   1. deploy the updated ui/state.py (save_grocers + _load_grocers_from_db)
--   2. the Grocer Hub "Save my stores" button will persist to DB on next click
--   3. sign-in will restore grocer selections without re-entering the wizard

-- =============================================================================
-- Migration 003 — Ledger: Honest Total Grocery Spend Tracking
-- =============================================================================
-- Adds three new columns to ledger_entries to track the full household grocery
-- bill separately from Found Money (meal plan savings).
--
-- Sincere Strategy: regulars + staples are shown on the dashboard and ledger
-- as "total grocery spend" but NEVER folded into the Found Money calculation,
-- which is purely about meal plan savings vs. single-store / HelloFresh.
--
-- Also adds trip_cost_est (gas) which was tracked in session_state but missing
-- from the DB schema.
-- =============================================================================

-- Full grocery spend breakdown
ALTER TABLE public.ledger_entries
  ADD COLUMN IF NOT EXISTS regulars_cost_est  numeric(8,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS staples_cost_est   numeric(8,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS total_spend_est    numeric(8,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS trip_cost_est      numeric(8,2) DEFAULT 0;

COMMENT ON COLUMN public.ledger_entries.regulars_cost_est IS
  'User-estimated weekly regulars spend (milk, eggs, bread, etc.) — not part of Found Money';
COMMENT ON COLUMN public.ledger_entries.staples_cost_est IS
  'Sum of household_staples items with cost entered — not part of Found Money';
COMMENT ON COLUMN public.ledger_entries.total_spend_est IS
  'Honest total grocery spend: whollyfare_cost_est + regulars_cost_est + staples_cost_est';
COMMENT ON COLUMN public.ledger_entries.trip_cost_est IS
  'Estimated gas cost for multi-store trips ($0.22/mile * 2 * distance)';

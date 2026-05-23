-- Migration 004: household_recipes table
-- Supports the Recipe Library page (12_Recipes.py)
-- Stores household favorites, family recipes, and web-found recipes.
--
-- POC:  Upsert via _sb_insert in state.py (conflict on household_id + recipe_id).
-- PROD: Add RLS policy so users only see their own household's recipes.

CREATE TABLE IF NOT EXISTS public.household_recipes (
    id              uuid            DEFAULT gen_random_uuid() PRIMARY KEY,
    household_id    uuid            NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
    recipe_id       text            NOT NULL,   -- library ID (e.g. "MEX-001") or "FAM-..." / "FIND-..."
    recipe_name     text            NOT NULL,
    is_favorite     boolean         NOT NULL DEFAULT false,
    source          text            NOT NULL DEFAULT 'library',  -- 'library' | 'family' | 'web'
    recipe_data     jsonb,          -- full recipe dict for family/web recipes; null for library refs
    created_at      timestamptz     NOT NULL DEFAULT now(),
    updated_at      timestamptz     NOT NULL DEFAULT now(),

    -- One row per household + recipe; re-insert toggles is_favorite
    CONSTRAINT household_recipes_hh_recipe_unique UNIQUE (household_id, recipe_id)
);

-- Keep updated_at current
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS household_recipes_updated_at ON public.household_recipes;
CREATE TRIGGER household_recipes_updated_at
    BEFORE UPDATE ON public.household_recipes
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Index for fast per-household lookups (the only query pattern in POC)
CREATE INDEX IF NOT EXISTS idx_household_recipes_hh
    ON public.household_recipes (household_id, is_favorite);

-- RLS (enable now, policies added in production)
ALTER TABLE public.household_recipes ENABLE ROW LEVEL SECURITY;

-- Permissive policy for POC (service_role key bypasses RLS anyway)
DROP POLICY IF EXISTS "service_role full access" ON public.household_recipes;
CREATE POLICY "service_role full access" ON public.household_recipes
    USING (true) WITH CHECK (true);

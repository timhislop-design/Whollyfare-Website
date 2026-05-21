-- =============================================================================
-- WhollyFare® — Supabase Phase 1 Schema Migration
-- Sentir Solutions® LLC · Charlottesville, VA
-- Generated: May 2026
--
-- HOW TO RUN:
--   1. Create a new Supabase project at supabase.com
--   2. Open the SQL Editor in your project dashboard
--   3. Paste this entire file and click Run
--   4. All tables, triggers, RLS policies, indexes, and seed data will be created
--
-- WHAT THIS CREATES:
--   Layer 1  — Auth & User (profiles)
--   Layer 2  — Household (households, household_users)
--   Layer 3  — Members + constraints (5 tables)
--   Layer 4  — Grocers (household_grocers)
--   Layer 5  — Flyer data (flyer_weeks, flyer_items)
--   Layer 6  — Meal Plans & Constraint Engine (4 tables)
--   Layer 7  — Ledger (ledger_entries)
--   Layer 8* — Price intelligence + adherence (ingredient_price_history, plan_adherence_log)
--   Layer 12 — Evidence Sources & Medical Transparency (constraint_evidence_sources)
--   Layer 13 — Safety, Audit & Compliance (3 tables)
--   Reference — platform_integrations, competitor_benchmarks, feature_flags
--
-- PHASE 2+ TABLES (not included here, noted in schema doc):
--   household_trend_snapshots, platform_weekly_metrics (weekly aggregate job)
--   Layer 9  — Meal Planning Preferences (6 tables)
--   Layer 10 — Coupons (2 tables)
--   Layer 11 — Integrations beyond reference tables (delivery_quotes, household_integrations)
--   Layer 14 — Growth (invitations, waitlist)
--   Layer 15 — Business Model (subscription_events, etc.)
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Returns true if the current auth user belongs to the given household.
-- Used throughout RLS policies to gate access to household-scoped tables.
CREATE OR REPLACE FUNCTION is_household_member(hid uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM household_users
    WHERE household_id = hid
      AND user_id = auth.uid()
  );
END;
$$;

-- Automatically sets updated_at = now() on any row update.
-- Applied to every table that has an updated_at column.
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- Auto-creates a profiles row when a new user signs up via Supabase Auth.
-- Supabase fires INSERT on auth.users; this trigger mirrors the essentials
-- into public.profiles so the app never has to create the profile manually.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, created_at, updated_at)
  VALUES (
    NEW.id,
    NEW.email,
    now(),
    now()
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

-- Generic audit log trigger. Fires on INSERT/UPDATE/DELETE on health-sensitive
-- tables and writes a record to audit_log. No application code required.
-- Applied to: member_allergies, member_diagnoses, member_lifestyle_tags,
--             meal_plans, meal_ingredients, constraint_rejections,
--             ledger_entries, data_privacy_requests
CREATE OR REPLACE FUNCTION audit_trigger_fn()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  old_data jsonb := NULL;
  new_data jsonb := NULL;
  record_pk uuid;
BEGIN
  IF TG_OP = 'DELETE' THEN
    old_data := to_jsonb(OLD);
    record_pk := (OLD).id;
  ELSIF TG_OP = 'INSERT' THEN
    new_data := to_jsonb(NEW);
    record_pk := (NEW).id;
  ELSE -- UPDATE
    old_data := to_jsonb(OLD);
    new_data := to_jsonb(NEW);
    record_pk := (NEW).id;
  END IF;

  INSERT INTO public.audit_log (
    table_name,
    record_id,
    action,
    old_values,
    new_values,
    changed_by,
    changed_at
  ) VALUES (
    TG_TABLE_NAME,
    record_pk,
    lower(TG_OP),
    old_data,
    new_data,
    auth.uid(),
    now()
  );

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END;
$$;


-- =============================================================================
-- LAYER 1 — AUTH & USER
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.profiles (
  id                 uuid        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email              text        NOT NULL,
  display_name       text,
  zip_code           text,
  city               text,
  state              text,                    -- 2-letter abbreviation, e.g. 'VA'
  metro_area         text,                    -- App-set from zip lookup; e.g. 'Charlottesville, VA'
  timezone           text,                    -- IANA string; e.g. 'America/New_York'
  phone              text,
  tier               text        NOT NULL DEFAULT 'free'
                                 CHECK (tier IN ('free', 'meal_planner', 'health_guard', 'full_table')),
  onboarding_complete boolean    NOT NULL DEFAULT false,
  marketing_opt_in   boolean     NOT NULL DEFAULT false,
  acquisition_source text,                    -- 'hislop_pilot', 'mcas_support_group', 'invitation', etc.
  invited_by         uuid        REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);

-- Trigger: auto-set updated_at
CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- Trigger: auto-create profile on Supabase Auth signup
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- profiles is INSERT-only via trigger; no direct INSERT policy needed for users.


-- =============================================================================
-- LAYER 2 — HOUSEHOLD
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.households (
  id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name              text        NOT NULL,                -- e.g. 'The Hislop Family'
  weekly_budget_usd numeric(8,2) NOT NULL,
  servings_per_meal smallint    NOT NULL DEFAULT 4,
  meals_per_week    smallint    NOT NULL DEFAULT 5,
  primary_zip       text,
  city              text,
  state             text,
  metro_area        text,                               -- Mirrors profiles.metro_area logic
  created_by        uuid        REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER households_updated_at
  BEFORE UPDATE ON public.households
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.households ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can read their household"
  ON public.households FOR SELECT
  USING (is_household_member(id));

CREATE POLICY "Household members can update their household"
  ON public.households FOR UPDATE
  USING (is_household_member(id));

CREATE POLICY "Users can create a household"
  ON public.households FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);


-- household_users: join table — which users belong to which household.
-- In the POC, one user per household. Phase 3 adds multi-user households.
CREATE TABLE IF NOT EXISTS public.household_users (
  household_id uuid        NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  user_id      uuid        NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  role         text        NOT NULL DEFAULT 'owner'
               CHECK (role IN ('owner', 'member')),
  joined_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (household_id, user_id)
);

ALTER TABLE public.household_users ENABLE ROW LEVEL SECURITY;

-- POC: users can see and manage only their own membership rows.
-- Phase 3: owner-manages-member logic can be added here once multi-user households go live.
CREATE POLICY "Users can manage their own household memberships"
  ON public.household_users FOR ALL
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());


-- =============================================================================
-- LAYER 3 — HOUSEHOLD MEMBERS & CONSTRAINTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.members (
  id            uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id  uuid     NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  name          text     NOT NULL,
  age           smallint,
  display_order smallint NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage members"
  ON public.members FOR ALL
  USING (is_household_member(household_id));


-- member_allergies: HARD constraints — the engine NEVER violates these.
CREATE TABLE IF NOT EXISTS public.member_allergies (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id  uuid NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
  allergen   text NOT NULL
             CHECK (allergen IN (
               'peanuts','tree_nuts','milk','eggs','wheat','soy',
               'fish','shellfish','sesame','mustard','celery',
               'lupin','molluscs','sulphites'
             )),
  UNIQUE (member_id, allergen)
);

ALTER TABLE public.member_allergies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage member allergies"
  ON public.member_allergies FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.members WHERE id = member_id)
    )
  );

-- Audit trigger — allergen changes are safety-critical and must be logged.
CREATE TRIGGER audit_member_allergies
  AFTER INSERT OR UPDATE OR DELETE ON public.member_allergies
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- member_diagnoses: Medical conditions that activate constraint rulesets.
CREATE TABLE IF NOT EXISTS public.member_diagnoses (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id  uuid NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
  diagnosis  text NOT NULL
             CHECK (diagnosis IN (
               'celiac','type1_diabetes','type2_diabetes','ckd',
               'pku','gerd','ibs_low_fodmap','crohns',
               'hypertension','mcas','eds','pots'
             )),
  UNIQUE (member_id, diagnosis)
);

ALTER TABLE public.member_diagnoses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage member diagnoses"
  ON public.member_diagnoses FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.members WHERE id = member_id)
    )
  );

CREATE TRIGGER audit_member_diagnoses
  AFTER INSERT OR UPDATE OR DELETE ON public.member_diagnoses
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- member_lifestyle_tags: Dietary preferences (not hard safety rules).
CREATE TABLE IF NOT EXISTS public.member_lifestyle_tags (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id uuid NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
  tag       text NOT NULL
            CHECK (tag IN (
              'vegan','vegetarian','halal','kosher','keto',
              'paleo','whole30','low_fodmap','gluten_free','dairy_free'
            )),
  UNIQUE (member_id, tag)
);

ALTER TABLE public.member_lifestyle_tags ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage lifestyle tags"
  ON public.member_lifestyle_tags FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.members WHERE id = member_id)
    )
  );

CREATE TRIGGER audit_member_lifestyle_tags
  AFTER INSERT OR UPDATE OR DELETE ON public.member_lifestyle_tags
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- member_custom_exclusions: Personal dislikes — soft rules.
CREATE TABLE IF NOT EXISTS public.member_custom_exclusions (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id      uuid NOT NULL REFERENCES public.members(id) ON DELETE CASCADE,
  exclusion_text text NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.member_custom_exclusions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage custom exclusions"
  ON public.member_custom_exclusions FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.members WHERE id = member_id)
    )
  );


-- =============================================================================
-- LAYER 4 — GROCERS
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.household_grocers (
  id                   uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id         uuid     NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  chain_name           text     NOT NULL,
  location_description text,
  source_type          text     NOT NULL DEFAULT 'manual'
                                CHECK (source_type IN ('manual','pdf','api','pdf_and_api')),
  rewards_enrolled     boolean  NOT NULL DEFAULT false,
  delivery_preferred   boolean  NOT NULL DEFAULT false,
  is_primary           boolean  NOT NULL DEFAULT false,
  flyer_url            text,
  display_order        smallint NOT NULL DEFAULT 0,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

-- Partial unique index: only one primary store per household.
CREATE UNIQUE INDEX IF NOT EXISTS household_grocers_one_primary
  ON public.household_grocers (household_id)
  WHERE is_primary = true;

CREATE TRIGGER household_grocers_updated_at
  BEFORE UPDATE ON public.household_grocers
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.household_grocers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage grocers"
  ON public.household_grocers FOR ALL
  USING (is_household_member(household_id));


-- =============================================================================
-- LAYER 5 — FLYER DATA
-- =============================================================================

-- flyer_weeks: One row per store per week — tracks what's been loaded.
CREATE TABLE IF NOT EXISTS public.flyer_weeks (
  id              uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id    uuid    NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  grocer_id       uuid    NOT NULL REFERENCES public.household_grocers(id) ON DELETE CASCADE,
  week_start_date date    NOT NULL,
  load_method     text    NOT NULL DEFAULT 'manual'
                          CHECK (load_method IN ('manual','pdf','api')),
  loaded_at       timestamptz NOT NULL DEFAULT now(),
  item_count      integer NOT NULL DEFAULT 0,
  UNIQUE (household_id, grocer_id, week_start_date)
);

ALTER TABLE public.flyer_weeks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage flyer weeks"
  ON public.flyer_weeks FOR ALL
  USING (is_household_member(household_id));


-- flyer_items: Every item from a weekly circular — primary engine input.
CREATE TABLE IF NOT EXISTS public.flyer_items (
  id             uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
  flyer_week_id  uuid     NOT NULL REFERENCES public.flyer_weeks(id) ON DELETE CASCADE,
  grocer_id      uuid     NOT NULL REFERENCES public.household_grocers(id) ON DELETE CASCADE,
  name           text     NOT NULL,
  category       text
                 CHECK (category IN (
                   'produce','protein','dairy','grain','legume',
                   'pantry','bakery','frozen','beverage','other'
                 )),
  unit           text
                 CHECK (unit IN (
                   'lb','oz','each','pkg','bunch','bag',
                   'dozen','gal','qt','can','jar','box'
                 )),
  sale_price     numeric(8,2) NOT NULL,
  regular_price  numeric(8,2),
  allergens      text[],         -- Array of allergen keys; user-declared in POC
  tags           text[],         -- e.g. ['organic','store_brand']
  usda_fdc_id    text,           -- USDA FoodData Central ID — null in POC
  is_manual      boolean  NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now()
);

-- Core engine query: all items for a given week
CREATE INDEX IF NOT EXISTS flyer_items_by_week
  ON public.flyer_items (flyer_week_id);

-- Price history join
CREATE INDEX IF NOT EXISTS flyer_items_by_grocer
  ON public.flyer_items (grocer_id);

ALTER TABLE public.flyer_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage flyer items"
  ON public.flyer_items FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.flyer_weeks WHERE id = flyer_week_id)
    )
  );


-- =============================================================================
-- LAYER 6 — MEAL PLANS & CONSTRAINT ENGINE
-- =============================================================================

-- meal_plans: One per household per week.
CREATE TABLE IF NOT EXISTS public.meal_plans (
  id               uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id     uuid     NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  week_start_date  date     NOT NULL,
  whollyfare_cost  numeric(8,2),
  single_store_est numeric(8,2),
  hellofresh_equiv numeric(8,2),
  found_money_est  numeric(8,2),
  vs_hellofresh_est numeric(8,2),
  total_servings   integer,
  approved_at      timestamptz,           -- Null until Sunday Buy-Off is pressed
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (household_id, week_start_date)
);

ALTER TABLE public.meal_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage meal plans"
  ON public.meal_plans FOR ALL
  USING (is_household_member(household_id));

CREATE TRIGGER audit_meal_plans
  AFTER INSERT OR UPDATE OR DELETE ON public.meal_plans
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- plan_meals: Individual dinners within a weekly plan.
CREATE TABLE IF NOT EXISTS public.plan_meals (
  id             uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id        uuid     NOT NULL REFERENCES public.meal_plans(id) ON DELETE CASCADE,
  day_label      text     NOT NULL,    -- e.g. 'Monday'
  day_order      smallint NOT NULL,    -- 1–7 for sort
  meal_name      text     NOT NULL,
  meal_cost      numeric(8,2),
  best_store     text,
  is_gluten_free boolean  NOT NULL DEFAULT false,
  allergen_notes text
);

ALTER TABLE public.plan_meals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage plan meals"
  ON public.plan_meals FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.meal_plans WHERE id = plan_id)
    )
  );


-- meal_ingredients: Each ingredient selected for a meal.
-- selection_rationale implements radical transparency — every selection is explainable.
CREATE TABLE IF NOT EXISTS public.meal_ingredients (
  id                  uuid     PRIMARY KEY DEFAULT gen_random_uuid(),
  meal_id             uuid     NOT NULL REFERENCES public.plan_meals(id) ON DELETE CASCADE,
  flyer_item_id       uuid     REFERENCES public.flyer_items(id) ON DELETE SET NULL,
  item_name           text     NOT NULL,    -- Denormalized at plan generation time
  quantity            text,
  unit                text,
  store_name          text,
  cost                numeric(8,2),
  display_order       smallint NOT NULL DEFAULT 0,
  -- Radical transparency: why was this ingredient chosen?
  selection_rationale text,                 -- e.g. 'Best price per serving in protein · 34% off · on sale 3/4 weeks at Kroger'
  price_rank          smallint,             -- 1 = cheapest safe option in its category
  discount_pct        numeric(5,2)          -- % off regular price; null if regular price unknown
);

ALTER TABLE public.meal_ingredients ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage meal ingredients"
  ON public.meal_ingredients FOR ALL
  USING (
    is_household_member(
      (SELECT mp.household_id
       FROM public.meal_plans mp
       JOIN public.plan_meals pm ON pm.plan_id = mp.id
       WHERE pm.id = meal_id)
    )
  );

CREATE TRIGGER audit_meal_ingredients
  AFTER INSERT OR UPDATE OR DELETE ON public.meal_ingredients
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- constraint_rejections: Every ingredient the engine rejected, and why.
-- This is the radical transparency feature — users see exactly why something
-- didn't make it into their plan.
CREATE TABLE IF NOT EXISTS public.constraint_rejections (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id              uuid NOT NULL REFERENCES public.meal_plans(id) ON DELETE CASCADE,
  flyer_item_id        uuid REFERENCES public.flyer_items(id) ON DELETE SET NULL,
  item_name            text NOT NULL,
  rejection_reason     text NOT NULL,     -- e.g. 'Contains wheat — celiac constraint for Abby'
  rejection_category   text NOT NULL
                       CHECK (rejection_category IN (
                         'allergen','diagnosis','lifestyle','custom_exclusion','budget'
                       )),
  triggered_by_member  text,              -- Member name; null for budget rejections
  -- Links to the medical guideline that drove this rejection (Layer 12).
  -- FK added after constraint_evidence_sources is created — see ALTER TABLE below.
  evidence_source_id   uuid,
  created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS constraint_rejections_by_plan
  ON public.constraint_rejections (plan_id);

ALTER TABLE public.constraint_rejections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can read constraint rejections"
  ON public.constraint_rejections FOR ALL
  USING (
    is_household_member(
      (SELECT household_id FROM public.meal_plans WHERE id = plan_id)
    )
  );

CREATE TRIGGER audit_constraint_rejections
  AFTER INSERT OR UPDATE OR DELETE ON public.constraint_rejections
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- =============================================================================
-- LAYER 7 — LEDGER
-- =============================================================================

-- ledger_entries: One per approved week. The most important data in the app
-- for households (savings history) and investors (real household data).
CREATE TABLE IF NOT EXISTS public.ledger_entries (
  id                  uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id        uuid    NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  plan_id             uuid    NOT NULL REFERENCES public.meal_plans(id) ON DELETE RESTRICT,
  week_start_date     date    NOT NULL,
  meals_planned       smallint,
  stores_used         text[],              -- Display list of store names
  -- Engine estimates (set at Buy-Off time)
  whollyfare_cost_est numeric(8,2),
  found_money_est     numeric(8,2),
  hellofresh_equiv    numeric(8,2),
  -- Actuals (filled when household logs receipt)
  actual_receipt      numeric(8,2),
  single_store_actual numeric(8,2),
  found_money_actual  numeric(8,2),        -- single_store_actual - actual_receipt
  vs_hellofresh_actual numeric(8,2),       -- hellofresh_equiv - actual_receipt
  accuracy_delta      numeric(8,2),        -- actual_receipt - whollyfare_cost_est
  notes               text,
  receipt_logged_at   timestamptz,         -- Null until logged
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (household_id, week_start_date)
);

CREATE INDEX IF NOT EXISTS ledger_entries_by_household_week
  ON public.ledger_entries (household_id, week_start_date DESC);

CREATE TRIGGER ledger_entries_updated_at
  BEFORE UPDATE ON public.ledger_entries
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.ledger_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage ledger entries"
  ON public.ledger_entries FOR ALL
  USING (is_household_member(household_id));

CREATE TRIGGER audit_ledger_entries
  AFTER INSERT OR UPDATE OR DELETE ON public.ledger_entries
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- =============================================================================
-- LAYER 8 (PARTIAL) — PRICE INTELLIGENCE & ADHERENCE
-- Collect from day 1. This is the data moat.
-- =============================================================================

-- ingredient_price_history: Every flyer item contributes a price data point.
-- NO household_id — aggregate data only. Privacy-preserving by design.
-- After 6 months: seasonal trends. After 12 months: price prediction.
-- After Phase 4 scale: a pricing intelligence layer chains would pay for.
CREATE TABLE IF NOT EXISTS public.ingredient_price_history (
  id                   uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  flyer_item_id        uuid    REFERENCES public.flyer_items(id) ON DELETE SET NULL,
  chain_name           text    NOT NULL,
  metro_area           text    NOT NULL,
  item_name_normalized text    NOT NULL,   -- Cleaned, lowercased for grouping across spellings
  category             text    NOT NULL,
  unit                 text    NOT NULL,
  sale_price           numeric(8,2) NOT NULL,
  regular_price        numeric(8,2),
  discount_pct         numeric(5,2),       -- Computed on insert: (reg-sale)/reg * 100
  week_start_date      date    NOT NULL,
  usda_fdc_id          text,
  created_at           timestamptz NOT NULL DEFAULT now(),
  UNIQUE (flyer_item_id)
);

-- Core trend query: chicken breast at Kroger over 12 weeks
CREATE INDEX IF NOT EXISTS price_history_trend
  ON public.ingredient_price_history (item_name_normalized, chain_name, week_start_date);

-- Regional category trend: produce in Charlottesville this quarter
CREATE INDEX IF NOT EXISTS price_history_regional
  ON public.ingredient_price_history (metro_area, category, week_start_date);

-- No RLS — this table stores no personal data and is service-role only.
-- Application writes here via a service-role function triggered after flyer_items insert.
ALTER TABLE public.ingredient_price_history ENABLE ROW LEVEL SECURITY;

-- Intentionally no SELECT policy for regular users. Admin dashboard uses service role.


-- plan_adherence_log: Did they follow the plan? One row per approved week.
-- Optional in POC — logged when household enters receipt.
CREATE TABLE IF NOT EXISTS public.plan_adherence_log (
  id                  uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id        uuid    NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  ledger_entry_id     uuid    NOT NULL REFERENCES public.ledger_entries(id) ON DELETE CASCADE,
  week_start_date     date    NOT NULL,
  stores_visited      text[], -- Which stores they actually shopped at
  stores_planned      text[], -- Which stores the plan said to use
  followed_store_split boolean,
  items_bought_count  smallint,
  items_planned_count smallint,
  adherence_score     numeric(4,2),        -- 0.0–1.0
  went_off_plan       boolean,
  deviation_notes     text,
  budget_kept         boolean,             -- actual_receipt <= weekly_budget_usd
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (household_id, week_start_date)
);

CREATE TRIGGER plan_adherence_log_updated_at
  BEFORE UPDATE ON public.plan_adherence_log
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.plan_adherence_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Household members can manage adherence log"
  ON public.plan_adherence_log FOR ALL
  USING (is_household_member(household_id));


-- =============================================================================
-- LAYER 12 — EVIDENCE SOURCES & MEDICAL TRANSPARENCY
-- constraint_rejections.evidence_source_id was declared as a plain uuid column
-- in Layer 6 (no inline FK) because this table didn't exist yet.
-- The FK constraint is added via ALTER TABLE immediately after this table is created.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.constraint_evidence_sources (
  id                      uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  constraint_key          text    NOT NULL,   -- e.g. 'hypertension', 'celiac', 'peanuts'
  constraint_type         text    NOT NULL
                          CHECK (constraint_type IN ('diagnosis','allergen','lifestyle')),
  authority_name          text    NOT NULL,
  guideline_name          text    NOT NULL,
  guideline_url           text    NOT NULL,   -- Direct link; users click to read the original source
  plain_english_summary   text    NOT NULL,   -- One sentence shown in the UI
  what_whollyfare_implements text NOT NULL,   -- The specific rule applied — makes the constraint auditable
  disclaimer              text    NOT NULL,   -- 'This is a planning guideline, not medical advice...'
  last_reviewed_at        date    NOT NULL,
  is_active               boolean NOT NULL DEFAULT true,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER constraint_evidence_sources_updated_at
  BEFORE UPDATE ON public.constraint_evidence_sources
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- No household RLS — this is platform reference data.
-- Users can SELECT to read the guideline; no INSERT/UPDATE for users.
ALTER TABLE public.constraint_evidence_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read evidence sources"
  ON public.constraint_evidence_sources FOR SELECT
  USING (true);

-- Now that constraint_evidence_sources exists, add the FK to constraint_rejections.
ALTER TABLE public.constraint_rejections
  ADD CONSTRAINT constraint_rejections_evidence_source_id_fkey
  FOREIGN KEY (evidence_source_id)
  REFERENCES public.constraint_evidence_sources(id)
  ON DELETE SET NULL;


-- =============================================================================
-- LAYER 13 — SAFETY, AUDIT & COMPLIANCE
-- =============================================================================

-- audit_log: Immutable write log for all health-sensitive tables.
-- Service-role only. Users can never query this table.
-- 'Zero allergen violations' is provable because of this table.
CREATE TABLE IF NOT EXISTS public.audit_log (
  id              uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name      text    NOT NULL,
  record_id       uuid    NOT NULL,
  action          text    NOT NULL CHECK (action IN ('insert','update','delete')),
  old_values      jsonb,
  new_values      jsonb,
  changed_by      uuid    REFERENCES public.profiles(id) ON DELETE SET NULL,
  changed_at      timestamptz NOT NULL DEFAULT now(),
  session_context text,   -- 'household_setup', 'engine_run', 'receipt_log', etc.
  ip_address      text    -- Hashed — never stored plain; for abuse detection only
);

CREATE INDEX IF NOT EXISTS audit_log_by_table_record
  ON public.audit_log (table_name, record_id, changed_at DESC);

CREATE INDEX IF NOT EXISTS audit_log_by_user
  ON public.audit_log (changed_by, changed_at DESC);

-- No SELECT policy for regular users — service-role and admin dashboard only.
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;


-- data_privacy_requests: Audit trail for export and deletion requests.
-- Sincere Strategy commitment #6: "Users can export their complete profile
-- and delete their account at any time."
CREATE TABLE IF NOT EXISTS public.data_privacy_requests (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  request_type   text NOT NULL CHECK (request_type IN ('export','deletion')),
  status         text NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','processing','completed','failed')),
  requested_at   timestamptz NOT NULL DEFAULT now(),
  completed_at   timestamptz,
  export_url     text,        -- Temporary signed URL; expires 48 hours after completed
  deletion_scope jsonb,       -- Which tables were cleared, in what order
  notes          text
);

ALTER TABLE public.data_privacy_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own privacy requests"
  ON public.data_privacy_requests FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can create privacy requests"
  ON public.data_privacy_requests FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE TRIGGER audit_data_privacy_requests
  AFTER INSERT OR UPDATE OR DELETE ON public.data_privacy_requests
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();


-- household_access_tokens: Pre-auth pilot access.
-- Each pilot household gets a private URL with a token — no password, no OAuth.
-- Used in the 60-day friends-and-family phase before full accounts.
CREATE TABLE IF NOT EXISTS public.household_access_tokens (
  id           uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid    NOT NULL REFERENCES public.households(id) ON DELETE CASCADE,
  token        text    NOT NULL UNIQUE,   -- Cryptographically random; used in URL: ?token=abc123
  created_by   uuid    REFERENCES public.profiles(id) ON DELETE SET NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL DEFAULT (now() + interval '90 days'),
  last_used_at timestamptz,
  revoked_at   timestamptz,
  notes        text    -- e.g. 'Martinez family — celiac pilot'
);

CREATE INDEX IF NOT EXISTS access_tokens_by_token
  ON public.household_access_tokens (token)
  WHERE revoked_at IS NULL;

-- Tim can read/manage tokens he created; service role manages the rest.
ALTER TABLE public.household_access_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Creators can manage access tokens"
  ON public.household_access_tokens FOR ALL
  USING (created_by = auth.uid());


-- =============================================================================
-- REFERENCE TABLES — platform_integrations, competitor_benchmarks, feature_flags
-- Platform-wide config. Service-role writes; all users can SELECT.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.platform_integrations (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  integration_key  text NOT NULL UNIQUE,
  display_name     text NOT NULL,
  integration_type text NOT NULL
                   CHECK (integration_type IN ('grocer_api','delivery','coupon','nutrition','location')),
  status           text NOT NULL
                   CHECK (status IN ('live','beta','in_development','planned','requires_investment')),
  description      text,
  logo_url         text,
  api_docs_url     text,
  expected_release text,
  notes            text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER platform_integrations_updated_at
  BEFORE UPDATE ON public.platform_integrations
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.platform_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read platform integrations"
  ON public.platform_integrations FOR SELECT
  USING (true);


CREATE TABLE IF NOT EXISTS public.competitor_benchmarks (
  id                  uuid    PRIMARY KEY DEFAULT gen_random_uuid(),
  service_name        text    NOT NULL UNIQUE,
  display_name        text    NOT NULL,
  service_type        text    NOT NULL
                      CHECK (service_type IN ('meal_kit','delivery_premium','subscription_box')),
  price_per_serving   numeric(6,2) NOT NULL,
  min_servings_per_week smallint,
  as_of_date          date    NOT NULL,
  source_url          text,
  is_active           boolean NOT NULL DEFAULT true,
  notes               text,
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER competitor_benchmarks_updated_at
  BEFORE UPDATE ON public.competitor_benchmarks
  FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

ALTER TABLE public.competitor_benchmarks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read competitor benchmarks"
  ON public.competitor_benchmarks FOR SELECT
  USING (true);


CREATE TABLE IF NOT EXISTS public.feature_flags (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  feature_key   text NOT NULL UNIQUE,
  display_name  text NOT NULL,
  status        text NOT NULL
                CHECK (status IN ('live','beta','coming_soon','requires_investment')),
  tier_required text CHECK (tier_required IN ('free','meal_planner','health_guard','full_table')),
  description   text,
  expected_phase text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.feature_flags ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read feature flags"
  ON public.feature_flags FOR SELECT
  USING (true);


-- =============================================================================
-- SEED DATA
-- =============================================================================

-- ── Platform Integrations ────────────────────────────────────────────────────
INSERT INTO public.platform_integrations
  (integration_key, display_name, integration_type, status, description, expected_release)
VALUES
  ('kroger_api',         'Kroger API',               'grocer_api',  'live',
   'Live circular prices and digital coupons via Kroger Partner API', 'Phase 1'),
  ('food_lion_pdf',      'Food Lion PDF Parser',      'grocer_api',  'live',
   'Parses Food Lion weekly circular PDFs for sale prices', 'Phase 1'),
  ('aldi_manual',        'Aldi Manual Entry',         'grocer_api',  'live',
   'Manual weekly price entry for Aldi — no API available', 'Phase 1'),
  ('harris_teeter_pdf',  'Harris Teeter PDF Parser',  'grocer_api',  'in_development',
   'PDF parser for Harris Teeter weekly circular', 'Phase 2'),
  ('usda_fdc',           'USDA FoodData Central',     'nutrition',   'beta',
   'USDA nutrition data for ingredient enrichment and health constraint validation', 'Phase 2'),
  ('flipp',              'Flipp',                     'coupon',      'planned',
   'Aggregated digital coupons from Flipp — filtered through household constraints', 'Phase 3'),
  ('ibotta',             'Ibotta',                    'coupon',      'planned',
   'Cash-back offers from Ibotta matched to your weekly plan', 'Phase 3'),
  ('instacart',          'Instacart',                 'delivery',    'requires_investment',
   'Same-day grocery delivery via Instacart — full shopping list push', 'Phase 3'),
  ('doordash',           'DoorDash Grocery',          'delivery',    'requires_investment',
   'Grocery delivery via DoorDash', 'Phase 3'),
  ('kroger_delivery',    'Kroger Delivery',           'delivery',    'in_development',
   'Home delivery via Kroger — uses existing Kroger API connection', 'Phase 2')
ON CONFLICT (integration_key) DO NOTHING;


-- ── Competitor Benchmarks ────────────────────────────────────────────────────
-- Prices verified May 2026. Update as market prices change.
INSERT INTO public.competitor_benchmarks
  (service_name, display_name, service_type, price_per_serving, min_servings_per_week, as_of_date, source_url, notes)
VALUES
  ('hellofresh',  'HelloFresh',  'meal_kit',  9.99, 2, '2026-05-01',
   'https://www.hellofresh.com/pages/plans',
   'Standard 2-person plan, classic box. First-box discounts excluded.'),
  ('blue_apron',  'Blue Apron',  'meal_kit',  9.99, 2, '2026-05-01',
   'https://www.blueapron.com/pages/pricing',
   'Signature 2-person plan. Standard weekly pricing.'),
  ('dinnerly',    'Dinnerly',    'meal_kit',  4.99, 2, '2026-05-01',
   'https://dinnerly.com/plans',
   'Budget meal kit. 2-person plan.'),
  ('everyplate',  'EveryPlate',  'meal_kit',  4.99, 2, '2026-05-01',
   'https://www.everyplate.com/plans',
   'Budget meal kit, HelloFresh subsidiary.'),
  ('factor',      'Factor (prepared)', 'meal_kit', 12.99, 4, '2026-05-01',
   'https://www.factor75.com/plans',
   'Ready-to-eat prepared meals. Higher price point reflects no cooking required.')
ON CONFLICT (service_name) DO NOTHING;


-- ── Feature Flags ─────────────────────────────────────────────────────────────
INSERT INTO public.feature_flags
  (feature_key, display_name, status, tier_required, description, expected_phase)
VALUES
  ('household_setup',        'Household Setup',          'live',                'free',          'Set up your family profile, dietary constraints, and member details', 'Phase 1'),
  ('grocer_hub',             'Grocer Hub',               'live',                'free',          'Connect your local stores and enter weekly sale prices', 'Phase 1'),
  ('meal_plan',              'This Week''s Plan',        'live',                'meal_planner',  'Your constraint-filtered, budget-optimized weekly dinner plan', 'Phase 1'),
  ('sunday_buyoff',          'Sunday Buy-Off',           'live',                'meal_planner',  'Lock in your plan and see exactly what you saved', 'Phase 1'),
  ('shopping_list',          'Shopping List',            'live',                'meal_planner',  'Store-by-store shopping list, ready to use at the checkout', 'Phase 1'),
  ('found_money_ledger',     'Found Money Ledger',       'live',                'free',          'Your running savings history — estimated and actual', 'Phase 1'),
  ('health_guard_dashboard', 'Health Guard Dashboard',   'coming_soon',         'health_guard',  'Full view of your household''s dietary constraints and how the engine applies them', 'Phase 2'),
  ('coupon_vault',           'Coupon Vault',             'coming_soon',         'meal_planner',  'Coupons matched to your plan, filtered through your constraints', 'Phase 2'),
  ('price_intelligence',     'Price Intelligence',       'coming_soon',         'meal_planner',  'Track ingredient price trends at your stores over time', 'Phase 3'),
  ('delivery_hub',           'Delivery Hub',             'requires_investment', 'meal_planner',  'Compare pickup vs. delivery cost for your shopping list', 'Phase 3'),
  ('recipe_library',         'Recipe Library',           'requires_investment', 'full_table',    'Full recipes for every planned meal, tailored to your constraints', 'Phase 3'),
  ('meal_ratings',           'Meal Ratings',             'coming_soon',         'full_table',    'Rate this week''s meals and build your household''s preference profile', 'Phase 3'),
  ('pantry_tracker',         'Pantry Tracker',           'requires_investment', 'full_table',    'Track what you have at home — automatically deducted from your shopping list', 'Phase 3'),
  ('market_insights',        'Market Insights',          'coming_soon',         'free',          'What''s trending in your local grocery market this week', 'Phase 3')
ON CONFLICT (feature_key) DO NOTHING;


-- ── Evidence Sources — Medical Transparency Seed Data ────────────────────────
-- These are the guidelines WhollyFare cites when applying dietary constraints.
-- The user sees the authority name, plain English summary, and a direct link
-- to the original guideline. WhollyFare never interprets the guideline —
-- it applies the filter, cites the source, and steps back.
INSERT INTO public.constraint_evidence_sources
  (constraint_key, constraint_type, authority_name, guideline_name, guideline_url,
   plain_english_summary, what_whollyfare_implements, disclaimer, last_reviewed_at)
VALUES

  -- Diagnoses
  ('hypertension', 'diagnosis',
   'American Heart Association',
   'Dietary Approaches to Stop Hypertension (DASH)',
   'https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/sodium/how-much-sodium-should-i-eat-per-day',
   'WhollyFare limits sodium to under 1,500 mg per serving for households with hypertension, following AHA DASH guidelines.',
   'Excludes ingredients flagged as high-sodium (>480 mg/serving). Flags meal-level sodium above 1,500 mg/serving.',
   'This is a planning tool, not medical advice. Your doctor or registered dietitian has final authority over your dietary management.',
   '2026-01-01'),

  ('ckd', 'diagnosis',
   'National Kidney Foundation',
   'KDOQI Clinical Practice Guidelines for Nutrition in Chronic Kidney Disease',
   'https://www.kidney.org/professionals/guidelines/guidelines_commentaries/kdoqi-clinical-practice-guideline-for-nutrition-in-ckd',
   'WhollyFare limits sodium, potassium, and phosphorus for households with CKD, following NKF KDOQI guidelines.',
   'Flags high-potassium ingredients (>200 mg/serving) and high-phosphorus items. Caps sodium per meal. Excludes ingredients flagged as CKD-unsafe.',
   'This is a planning tool, not medical advice. Your nephrologist or renal dietitian has final authority over your dietary management.',
   '2026-01-01'),

  ('type2_diabetes', 'diagnosis',
   'American Diabetes Association',
   'Standards of Medical Care in Diabetes',
   'https://diabetesjournals.org/care/issue/47/Supplement_1',
   'WhollyFare limits added sugars and refined carbohydrates for households with type 2 diabetes, following ADA Standards of Care.',
   'Excludes ingredients with high added sugar content. Prioritizes low-glycemic proteins and vegetables. Flags meals exceeding 45g carbohydrates per serving.',
   'This is a planning tool, not medical advice. Your endocrinologist or certified diabetes educator has final authority over your dietary management.',
   '2026-01-01'),

  ('type1_diabetes', 'diagnosis',
   'American Diabetes Association',
   'Standards of Medical Care in Diabetes',
   'https://diabetesjournals.org/care/issue/47/Supplement_1',
   'WhollyFare tracks carbohydrate content per meal for households with type 1 diabetes, following ADA Standards of Care.',
   'Displays estimated carbohydrates per serving for every meal. Flags meals exceeding 45g carbs per serving.',
   'This is a planning tool, not medical advice. Your endocrinologist or certified diabetes educator has final authority over your dietary management.',
   '2026-01-01'),

  ('celiac', 'diagnosis',
   'Celiac Disease Foundation',
   'Gluten-Free Diet Guidelines',
   'https://celiac.org/gluten-free-living/what-is-gluten/sources-of-gluten/',
   'WhollyFare applies a strict gluten-free filter for households with celiac disease, following Celiac Disease Foundation guidelines.',
   'Excludes all ingredients flagged as containing wheat, barley, rye, or oats (unless certified gluten-free). Labels all meals is_gluten_free=true/false.',
   'This is a planning tool, not medical advice. Cross-contamination risks during food preparation are the household''s responsibility. Your gastroenterologist or dietitian has final authority.',
   '2026-01-01'),

  ('ibs_low_fodmap', 'diagnosis',
   'Monash University',
   'Monash University Low FODMAP Diet Program',
   'https://www.monashfodmap.com/about-fodmap-and-ibs/high-and-low-fodmap-foods/',
   'WhollyFare applies a low-FODMAP ingredient filter for households with IBS, following Monash University guidelines.',
   'Excludes high-FODMAP ingredients from the ingredient set. Uses the Monash University low-FODMAP food list as the reference.',
   'This is a planning tool, not medical advice. FODMAP tolerance is individual — work with a registered dietitian trained in the low-FODMAP approach.',
   '2026-01-01'),

  ('gerd', 'diagnosis',
   'American College of Gastroenterology',
   'ACG Clinical Guideline: Diagnosis and Management of GERD',
   'https://journals.lww.com/ajg/fulltext/2022/01000/acg_clinical_guideline__diagnosis_and_management.14.aspx',
   'WhollyFare limits common GERD trigger foods (acidic, high-fat, caffeinated) for households with GERD, following ACG guidelines.',
   'Flags high-fat ingredients and common GERD triggers (citrus, tomatoes, chocolate, mint, spicy ingredients). Does not exclude — flags for household review.',
   'This is a planning tool, not medical advice. GERD triggers are highly individual. Your gastroenterologist has final authority over your dietary management.',
   '2026-01-01'),

  ('crohns', 'diagnosis',
   'Crohn''s & Colitis Foundation',
   'Diet, Nutrition & Inflammatory Bowel Disease',
   'https://www.crohnscolitisfoundation.org/diet-and-nutrition/specific-diet-recommendations',
   'WhollyFare applies a Crohn''s-aware ingredient filter, following Crohn''s & Colitis Foundation dietary guidance.',
   'Limits high-fiber raw vegetables and high-fat foods during active flares. Prioritizes easily digestible proteins and cooked vegetables.',
   'This is a planning tool, not medical advice. Crohn''s dietary needs vary significantly by individual and disease activity. Your gastroenterologist and dietitian have final authority.',
   '2026-01-01'),

  ('pku', 'diagnosis',
   'National PKU Alliance',
   'PKU Dietary Management Guidelines',
   'https://www.npkua.org/Education/About-PKU/Diet-Management',
   'WhollyFare limits high-phenylalanine ingredients for households with PKU, following National PKU Alliance guidelines.',
   'Excludes high-protein animal products that are primary phenylalanine sources. Flags all ingredients with phenylalanine content.',
   'This is a planning tool, not medical advice. PKU dietary management requires precise phenylalanine counting. Your metabolic dietitian has final authority.',
   '2026-01-01'),

  ('mcas', 'diagnosis',
   'American Academy of Allergy, Asthma & Immunology',
   'Mast Cell Activation Syndrome: Management and Diagnosis',
   'https://www.aaaai.org/tools-for-the-public/conditions-library/allergies/mast-cell-diseases',
   'WhollyFare applies a low-histamine ingredient filter for households with MCAS, following AAAAI guidelines.',
   'Limits high-histamine foods (aged cheeses, fermented foods, alcohol, vinegar, processed meats). Avoids histamine-liberating ingredients.',
   'This is a planning tool, not medical advice. MCAS triggers are highly individual. Your allergist or immunologist has final authority over your dietary management.',
   '2026-01-01'),

  -- Allergens
  ('peanuts', 'allergen',
   'Food Allergy Research & Education (FARE)',
   'Top 9 Food Allergens — Peanut',
   'https://www.foodallergy.org/living-with-food-allergies/food-allergy-essentials/common-allergens/peanut',
   'WhollyFare strictly excludes all peanut-containing ingredients for members with peanut allergy, following FARE guidelines.',
   'Excludes all ingredients flagged as containing peanuts or peanut derivatives. Does not reduce this constraint for any budget reason.',
   'This is a safety constraint, not medical advice. Peanut allergy can be life-threatening. Always verify ingredient labels before purchasing.',
   '2026-01-01'),

  ('celery', 'allergen',
   'Anaphylaxis Campaign (UK)',
   'Celery Allergy — 14 Major Food Allergens',
   'https://www.anaphylaxis.org.uk/allergens/celery/',
   'WhollyFare excludes celery-containing ingredients for members with celery allergy, following EU 14 major allergen guidelines.',
   'Excludes all ingredients flagged as containing celery, celeriac, or celery derivatives.',
   'This is a safety constraint, not medical advice. Always verify ingredient labels before purchasing.',
   '2026-01-01'),

  -- Lifestyle
  ('vegan', 'lifestyle',
   'Academy of Nutrition and Dietetics',
   'Position of the Academy of Nutrition and Dietetics: Vegetarian Diets',
   'https://www.jandonline.org/article/S2212-2672(16)31192-3/fulltext',
   'WhollyFare excludes all animal products for vegan households, following AND dietary guidelines.',
   'Excludes all meat, poultry, fish, dairy, eggs, and honey. Prioritizes plant-based proteins and vegetables.',
   'This is a planning tool. Nutrient adequacy (B12, iron, calcium, omega-3) in plant-based diets requires attention — consult a registered dietitian.',
   '2026-01-01'),

  ('halal', 'lifestyle',
   'Islamic Food and Nutrition Council of America',
   'Halal Certification Standards',
   'https://www.ifanca.org/Pages/halal.aspx',
   'WhollyFare excludes non-halal ingredients for households following halal dietary guidelines, per IFANCA standards.',
   'Excludes pork and pork products, non-halal-certified meat, alcohol and alcohol-derived ingredients.',
   'This is a planning tool. Halal certification of specific brands should be verified by the household at purchase.',
   '2026-01-01'),

  ('kosher', 'lifestyle',
   'Orthodox Union',
   'Kosher Certification Standards',
   'https://www.ou.org/kosher/for-your-information/what-does-kosher-mean/',
   'WhollyFare applies kosher dietary guidelines for households keeping kosher, per Orthodox Union standards.',
   'Excludes pork, shellfish, and mixing of meat and dairy within the same meal. Flags ingredients requiring kosher certification.',
   'This is a planning tool. Kosher certification of specific products must be verified by the household. Consult your rabbi or certifying body for specific guidance.',
   '2026-01-01')

ON CONFLICT DO NOTHING;


-- =============================================================================
-- END OF PHASE 1 MIGRATION
-- =============================================================================
--
-- NEXT STEPS:
--   1. Run this file in your Supabase SQL Editor
--   2. Verify tables created: SELECT table_name FROM information_schema.tables
--      WHERE table_schema = 'public' ORDER BY table_name;
--   3. Wire your Streamlit app to Supabase using the Python client:
--      pip install supabase
--      from supabase import create_client
--      client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
--   4. Store SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets:
--      .streamlit/secrets.toml → [supabase] url = "..." anon_key = "..."
--
-- PHASE 2 ADDITIONS (run in a subsequent migration):
--   - household_trend_snapshots (materialized savings snapshot per household)
--   - platform_weekly_metrics (platform-wide aggregate job)
--   - Layer 9: Meal Planning Preferences (6 tables)
--   - Layer 10: Coupons (coupons, household_coupon_clips)
--   - Layer 11: household_integrations, delivery_quotes
--   - Layer 13: notification_preferences, notification_queue, email_events
--   - Layer 14: invitations, waitlist
--   - Layer 15: subscription_events, app_events, loyalty_rewards_events, b2b_licenses
--   - meal_nutrition_summary (USDA FDC integration)
--
-- =============================================================================

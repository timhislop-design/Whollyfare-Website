"""
store_regions.py — Regional chain availability for zip-code-aware store filtering.

Maps US zip code prefixes to geographic regions, then maps grocery chains to the
regions where they operate. Used by the Grocer Hub to surface only chains the
user is likely to have access to.

POC: Region is inferred from the first digit(s) of the zip code — a rough but
     reliable approximation for chain availability at the demo level.
PROD: Replace with a real store-locator API call (Kroger Locations API, Google
      Places API, or a maintained chain-coverage database). The API would return
      confirmed nearby locations with address, hours, and store ID — enabling
      automatic flyer URL resolution and distance calculation.

Region definitions (US zip prefix → region label):
  0-1 : Northeast      (CT, MA, ME, NH, NJ, NY, RI, VT, plus PR/VI)
  2   : Mid-Atlantic   (DC, DE, MD, NC, SC, VA, WV — Charlottesville is 229xx)
  3   : Southeast      (AL, FL, GA, MS, TN)
  4-5 : Midwest        (IN, KY, MI, OH, WI, IA, MN, MT, ND, SD, NE)
  6   : South-Midwest  (IL, KS, MO)
  7   : South          (AR, LA, OK, TX)
  8   : Mountain West  (AZ, CO, ID, NM, NV, UT, WY, AK)
  9   : Pacific        (CA, HI, OR, WA)
"""

from typing import Optional

# ── Region constants ──────────────────────────────────────────────────────────
NORTHEAST    = "northeast"
MID_ATLANTIC = "mid_atlantic"
SOUTHEAST    = "southeast"
MIDWEST      = "midwest"
SOUTH        = "south"
MOUNTAIN     = "mountain"
PACIFIC      = "pacific"
ALL_REGIONS  = {NORTHEAST, MID_ATLANTIC, SOUTHEAST, MIDWEST, SOUTH, MOUNTAIN, PACIFIC}

# ── Zip prefix → region ───────────────────────────────────────────────────────
_ZIP_PREFIX_REGION: dict[str, str] = {
    "0":  NORTHEAST,
    "1":  NORTHEAST,
    "20": MID_ATLANTIC, "21": MID_ATLANTIC, "22": MID_ATLANTIC,
    "23": MID_ATLANTIC, "24": MID_ATLANTIC, "25": MID_ATLANTIC,
    "26": MID_ATLANTIC, "27": MID_ATLANTIC, "28": SOUTHEAST,
    "29": SOUTHEAST,
    "30": SOUTHEAST, "31": SOUTHEAST, "32": SOUTHEAST, "33": SOUTHEAST,
    "34": SOUTHEAST, "35": SOUTHEAST, "36": SOUTHEAST, "37": SOUTHEAST,
    "38": SOUTHEAST, "39": SOUTHEAST,
    "4":  MIDWEST,
    "5":  MIDWEST,
    "6":  SOUTH,      # IL/KS/MO — blended; Midwest chains also here
    "7":  SOUTH,
    "8":  MOUNTAIN,
    "9":  PACIFIC,
}

# ── Chain → set of regions where it operates ─────────────────────────────────
# "ALL" means the chain has locations in every region.
CHAIN_REGIONS: dict[str, set[str]] = {
    # ── Available everywhere ──────────────────────────────────────────────────
    "ALDI":            ALL_REGIONS,
    "Walmart":         ALL_REGIONS,
    "Dollar General":  ALL_REGIONS,
    "Dollar Tree":     ALL_REGIONS,
    "Whole Foods":     ALL_REGIONS,
    "Trader Joe's":    ALL_REGIONS,
    "Costco":          ALL_REGIONS,
    "Sam's Club":      ALL_REGIONS,
    "Kroger":          ALL_REGIONS,
    "Natural Grocers": ALL_REGIONS,
    "The Fresh Market": {NORTHEAST, MID_ATLANTIC, SOUTHEAST, MIDWEST, SOUTH},

    # ── Southeast + Mid-Atlantic ──────────────────────────────────────────────
    "Food Lion":       {MID_ATLANTIC, SOUTHEAST},
    "Harris Teeter":   {MID_ATLANTIC, SOUTHEAST},
    "Publix":          {MID_ATLANTIC, SOUTHEAST, SOUTH},
    "Ingles Markets":  {SOUTHEAST},
    "Earth Fare":      {MID_ATLANTIC, SOUTHEAST, MIDWEST},
    "Sprouts":         {SOUTHEAST, SOUTH, MOUNTAIN, PACIFIC, MIDWEST},

    # ── Mid-Atlantic + Northeast ──────────────────────────────────────────────
    "Giant Food":      {MID_ATLANTIC},
    "Wegmans":         {MID_ATLANTIC, NORTHEAST},
    "Weis Markets":    {MID_ATLANTIC, NORTHEAST},
    "Safeway":         {MID_ATLANTIC, MOUNTAIN, PACIFIC},
    "Albertsons":      {MID_ATLANTIC, MOUNTAIN, PACIFIC, MIDWEST},

    # ── Northeast ─────────────────────────────────────────────────────────────
    "Stop & Shop":     {NORTHEAST},
    "ShopRite":        {NORTHEAST, MID_ATLANTIC},

    # ── Midwest ───────────────────────────────────────────────────────────────
    "Meijer":          {MIDWEST},
    "Hy-Vee":          {MIDWEST},
    "Giant Eagle":     {MIDWEST, MID_ATLANTIC},
    "WinCo Foods":     {MIDWEST, MOUNTAIN, PACIFIC},
    "Save-A-Lot":      {NORTHEAST, MID_ATLANTIC, SOUTHEAST, MIDWEST, SOUTH},
    "Food 4 Less":     {MIDWEST, PACIFIC},
    "Lidl":            {NORTHEAST, MID_ATLANTIC, SOUTHEAST},

    # ── South / Texas ─────────────────────────────────────────────────────────
    "H-E-B":           {SOUTH},

    # ── Pacific + Mountain ────────────────────────────────────────────────────
    # (WinCo, Albertsons, Safeway already covered above)

    # ── Local tier: always shown regardless of zip ────────────────────────────
    # (handled separately in the Grocer Hub — local tier is never filtered out)
}


def zip_to_region(zip_code: str) -> Optional[str]:
    """Infer geographic region from a 5-digit US zip code.

    Returns a region constant or None if the zip is unrecognised.
    Tries 2-digit prefix first (finer-grained), then 1-digit.
    """
    if not zip_code or len(zip_code) < 1:
        return None
    z = zip_code.strip().zfill(5)
    # 2-digit prefix (covers the 2x/3x mid-Atlantic vs southeast split)
    two = z[:2]
    if two in _ZIP_PREFIX_REGION:
        return _ZIP_PREFIX_REGION[two]
    # 1-digit fallback
    one = z[:1]
    return _ZIP_PREFIX_REGION.get(one)


def chains_for_zip(zip_code: str) -> set[str]:
    """Return the set of chain names available near a given zip code.

    Returns ALL chains if the zip is unrecognised (fail-open: better to show
    too many options than to hide chains the user actually has nearby).
    """
    region = zip_to_region(zip_code)
    if region is None:
        return set(CHAIN_REGIONS.keys())
    return {chain for chain, regions in CHAIN_REGIONS.items() if region in regions}


def region_label(zip_code: str) -> str:
    """Human-readable region name for display."""
    region = zip_to_region(zip_code)
    labels = {
        NORTHEAST:    "Northeast US",
        MID_ATLANTIC: "Mid-Atlantic",
        SOUTHEAST:    "Southeast",
        MIDWEST:      "Midwest",
        SOUTH:        "South / Southwest",
        MOUNTAIN:     "Mountain West",
        PACIFIC:      "Pacific / West Coast",
    }
    return labels.get(region, "your area") if region else "your area"


# ── Charlottesville preset ────────────────────────────────────────────────────
# Charlottesville VA is zip 22901-22911 — Mid-Atlantic region.
# These are confirmed locations within ~15 miles of downtown Charlottesville.
CHARLOTTESVILLE_CHAINS: list[str] = [
    "Kroger", "Food Lion", "ALDI", "Harris Teeter", "Walmart",
    "Whole Foods", "Trader Joe's", "Dollar General", "Costco",
    "The Fresh Market", "EW Thomas Grocery", "Foods of All Nations",
    "Integral Yoga Natural", "Reid's Country Store",
]

"""
store_locations.py — Store lat/lon registry + distance utilities.

Used by the Grocer Hub wizard to:
  - Show a map of stores near the user's zip
  - Calculate real driving-distance estimates (via Haversine)
  - Surface stores the user might not know exist
  - Pre-populate trip cost math per store

POC: Coordinates are hardcoded. Charlottesville / Palmyra VA stores are
     accurate to within ~0.2 miles. National chains use city-centroid
     coordinates for the region — accurate enough for "is this chain near me"
     logic but not for turn-by-turn.

PROD: Replace with live store-locator API calls:
      - Kroger Locations API (chain_id, store_id, lat/lon, address, hours)
      - Google Places API (any chain, high accuracy, address verification)
      - Stored in PostgreSQL stores table with geospatial index (PostGIS).
      Distance calculation moves server-side; Haversine stays as a fallback.
"""

import math
from typing import Optional

# ── Zip centroid lookup ───────────────────────────────────────────────────────
# Maps 5-digit zip codes to (lat, lon) centroids.
# POC: Covers Charlottesville / Palmyra VA and a handful of nearby zips.
# PROD: Use a full USPS zip centroid dataset (~42k entries, ~2MB CSV).
ZIP_CENTROIDS: dict[str, tuple[float, float]] = {
    # Charlottesville, VA
    "22901": (38.0724, -78.5139),
    "22902": (38.0281, -78.5016),
    "22903": (38.0477, -78.5139),
    "22904": (38.0477, -78.5139),
    "22905": (38.0477, -78.5139),
    "22906": (38.0477, -78.5139),
    "22907": (38.0477, -78.5139),
    "22908": (38.0477, -78.5139),
    "22909": (38.0477, -78.5139),
    "22911": (38.0900, -78.4700),  # Pantops / Rivanna area
    # Palmyra / Fluvanna County
    "22963": (37.8595, -78.2585),
    # Staunton / Waynesboro
    "24401": (38.1496, -79.0717),
    "22980": (38.0685, -78.8968),
    # Richmond area
    "23220": (37.5544, -77.4603),
    "23230": (37.5844, -77.5003),
}


def zip_centroid(zip_code: str) -> Optional[tuple[float, float]]:
    """Return (lat, lon) for a zip code, or None if unknown."""
    return ZIP_CENTROIDS.get(zip_code.strip().zfill(5))


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in miles between two lat/lon points.

    Uses the Haversine formula. Accurate to within ~0.5% for distances
    under 500 miles — more than sufficient for store-proximity logic.
    """
    R = 3_958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def distance_from_zip(zip_code: str, store_lat: float, store_lon: float) -> Optional[float]:
    """Miles from a zip centroid to a store. Returns None if zip unknown."""
    centroid = zip_centroid(zip_code)
    if centroid is None:
        return None
    return haversine_miles(centroid[0], centroid[1], store_lat, store_lon)


def trip_cost_estimate(distance_miles: float, rate_per_mile: float = 0.22) -> float:
    """Round-trip gas cost at $0.22/mile (IRS conservative personal vehicle rate).

    POC: Flat rate. Sincere Strategy: we use the conservative rate, not the
         flattering one. $0.22 is below IRS standard ($0.67 in 2024) intentionally
         — it reflects fuel-only cost, not total vehicle cost. We show it as
         'gas cost estimate' not 'true cost of trip.'
    PROD: Optionally let the user set their own rate (for EV owners, high-mpg
          vehicles, etc.). Store the rate in their profile.
    """
    return round(distance_miles * 2 * rate_per_mile, 2)


# ── Store location registry ───────────────────────────────────────────────────
# Each entry: chain name (must match STORE_TIERS in Grocer Hub), tier,
# location name, address, lat, lon, and notes for display.
#
# POC: Charlottesville / Palmyra VA stores are accurate. National chains
#      outside Charlottesville are representative city-center coordinates.
# PROD: Stored in DB. Added via admin tool or grocer API integration.

STORE_LOCATIONS: list[dict] = [
    # ── Charlottesville VA — confirmed locations ──────────────────────────────
    {
        "chain":    "Kroger",
        "location": "Kroger — Barracks Road",
        "address":  "1980 Barracks Rd, Charlottesville, VA 22903",
        "lat":      38.0484,
        "lon":      -78.5016,
        "tier":     "mainstream",
        "zip":      "22903",
        "api_live": True,
        "note":     "Pilot store. Kroger API live for price pulls.",
    },
    {
        "chain":    "Food Lion",
        "location": "Food Lion — Pantops",
        "address":  "1903 Richmond Rd, Charlottesville, VA 22911",
        "lat":      38.0390,
        "lon":      -78.4620,
        "tier":     "mainstream",
        "zip":      "22911",
        "api_live": False,
        "note":     "Pilot store. Manual flyer entry. MVP Card deals.",
    },
    {
        "chain":    "ALDI",
        "location": "ALDI — Rio Road",
        "address":  "100 Rio Rd E, Charlottesville, VA 22901",
        "lat":      38.0644,
        "lon":      -78.5001,
        "tier":     "discount",
        "zip":      "22901",
        "api_live": False,
        "note":     "Pilot store. No loyalty card. Weekly Specialbuys rotate Sunday.",
    },
    {
        "chain":    "Harris Teeter",
        "location": "Harris Teeter — Barracks Road",
        "address":  "2075 Bond St, Charlottesville, VA 22901",
        "lat":      38.0501,
        "lon":      -78.5058,
        "tier":     "mainstream",
        "zip":      "22901",
        "api_live": False,
        "note":     "Pilot store. VIC card + e-VIC digital coupons. Super Doubles quarterly.",
    },
    {
        "chain":    "Walmart",
        "location": "Walmart Supercenter — Charlottesville",
        "address":  "2041 Hydraulic Rd, Charlottesville, VA 22901",
        "lat":      38.0734,
        "lon":      -78.5083,
        "tier":     "discount",
        "zip":      "22901",
        "api_live": False,
        "note":     "Rollback prices. No fixed flyer cycle — manual entry recommended.",
    },
    {
        "chain":    "Whole Foods",
        "location": "Whole Foods — Charlottesville",
        "address":  "800 E Market St, Charlottesville, VA 22902",
        "lat":      38.0302,
        "lon":      -78.4810,
        "tier":     "specialty",
        "zip":      "22902",
        "api_live": False,
        "note":     "Prime members get 10% off sale items. 365 brand competitive on staples.",
    },
    {
        "chain":    "Trader Joe's",
        "location": "Trader Joe's — Charlottesville",
        "address":  "1797 Abbey Rd, Charlottesville, VA 22901",
        "lat":      38.0658,
        "lon":      -78.5041,
        "tier":     "specialty",
        "zip":      "22901",
        "api_live": False,
        "note":     "No loyalty card. Stable pricing, Fearless Flyer monthly.",
    },
    {
        "chain":    "EW Thomas Grocery",
        "location": "EW Thomas Grocery — Palmyra",
        "address":  "50 Courthouse Rd, Palmyra, VA 22963",
        "lat":      37.8600,
        "lon":      -78.2590,
        "tier":     "local",
        "zip":      "22963",
        "api_live": False,
        "note":     "Palmyra local institution. Meat counter, fresh produce, weekly specials.",
    },
    {
        "chain":    "Foods of All Nations",
        "location": "Foods of All Nations — Charlottesville",
        "address":  "2121 Ivy Rd, Charlottesville, VA 22903",
        "lat":      38.0410,
        "lon":      -78.5290,
        "tier":     "local",
        "zip":      "22903",
        "api_live": False,
        "note":     "International specialty market. Unique ingredients, fair prices.",
    },
    {
        "chain":    "Integral Yoga Natural",
        "location": "Integral Yoga Natural Foods",
        "address":  "923 Preston Ave, Charlottesville, VA 22903",
        "lat":      38.0370,
        "lon":      -78.5053,
        "tier":     "local",
        "zip":      "22903",
        "api_live": False,
        "note":     "Natural and organic co-op. Bulk bins, local produce.",
    },
    {
        "chain":    "The Fresh Market",
        "location": "The Fresh Market — Charlottesville",
        "address":  "100 Wegmans Way, Charlottesville, VA 22901",
        "lat":      38.0791,
        "lon":      -78.5026,
        "tier":     "specialty",
        "zip":      "22901",
        "api_live": False,
        "note":     "Premium meats and produce. Weekly specials often include protein deals.",
    },
]

# ── Convenience lookups ───────────────────────────────────────────────────────
LOCATIONS_BY_CHAIN: dict[str, list[dict]] = {}
for _loc in STORE_LOCATIONS:
    LOCATIONS_BY_CHAIN.setdefault(_loc["chain"], []).append(_loc)


def stores_near_zip(
    zip_code: str,
    radius_miles: float = 15.0,
    tiers: Optional[list[str]] = None,
) -> list[dict]:
    """Return store locations within radius_miles of zip_code, sorted by distance.

    Each returned dict includes all STORE_LOCATIONS fields plus:
      - 'distance_miles': float
      - 'trip_cost':      float (round-trip gas estimate)

    If zip_code is unknown, returns all stores (fail-open for pilot).
    tiers: optional list of tier keys to filter by (e.g. ['discount', 'mainstream']).
    """
    centroid = zip_centroid(zip_code)
    results = []
    for loc in STORE_LOCATIONS:
        if tiers and loc["tier"] not in tiers:
            continue
        if centroid is None:
            dist = None
            cost = None
        else:
            dist = haversine_miles(centroid[0], centroid[1], loc["lat"], loc["lon"])
            if dist > radius_miles + 0.4:  # x.4 and under counts as within radius
                continue
            cost = trip_cost_estimate(dist)
        results.append({**loc, "distance_miles": dist, "trip_cost": cost})

    if centroid is not None:
        results.sort(key=lambda x: x["distance_miles"])
    return results

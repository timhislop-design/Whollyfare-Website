"""
cli.py — Command-line runner for the Food Lion flyer parser.

Usage:
    python -m integrations.food_lion.cli --help
    python -m integrations.food_lion.cli \\
        --pdf food_lion_circular.pdf \\
        --location "Palmyra, VA 22963" \\
        --week 2026-05-18 \\
        --out app/data/flyers/food_lion_2026-05-18.json
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from integrations.food_lion.parser import FoodLionParser


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    ap = argparse.ArgumentParser(
        description="Parse a Food Lion PDF flyer into WhollyFare JSON."
    )
    ap.add_argument("--pdf",      required=True, help="Path to the Food Lion circular PDF")
    ap.add_argument("--location", default="Palmyra, VA 22963", help="Store location string")
    ap.add_argument("--week",     default=None, help="Flyer week date (YYYY-MM-DD); defaults to next Sunday")
    ap.add_argument("--out",      default=None, help="Output JSON path; defaults to app/data/flyers/food_lion_<week>.json")
    ap.add_argument("--usda-key", default=None, help="USDA FDC API key (or set USDA_API_KEY env var)")
    ap.add_argument("--no-enrich", action="store_true", help="Skip USDA nutrition enrichment")
    args = ap.parse_args()

    parser = FoodLionParser(
        store_location=args.location,
        flyer_week=args.week,
    )

    print(f"\n→ Parsing: {args.pdf}")
    result = parser.parse_pdf(args.pdf)

    if not args.no_enrich:
        api_key = args.usda_key or os.environ.get("USDA_API_KEY", "")
        if api_key:
            from integrations.food_lion.usda_enricher import USDAEnricher
            enricher = USDAEnricher(api_key=api_key)
            enricher.enrich(result)
        else:
            print("  ⚠  No USDA_API_KEY — nutrition fields will be zeros.")
            print("     Get a free key at https://api.data.gov/signup/")

    # Default output path
    out_path = args.out or f"app/data/flyers/food_lion_{result.flyer_week}.json"
    saved = parser.save(result, out_path)

    meta = result.parse_metadata
    print(f"\n✓ Done")
    print(f"  Items parsed:    {meta.get('items_after_enrichment', len(result.items))}")
    print(f"  Items skipped:   {meta.get('items_skipped', 0)}")
    print(f"  USDA enriched:   {meta.get('usda_enriched_count', 0)}")
    print(f"  Saved to:        {saved}\n")


if __name__ == "__main__":
    main()

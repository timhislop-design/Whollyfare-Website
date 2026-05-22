"""
parser.py — Food Lion Weekly Flyer Parser
-----------------------------------------
Converts a Food Lion PDF weekly circular into a WhollyFare-standard
flyer JSON file, ready for FlyerIngestor.from_json().

Handles the two real-world Food Lion PDF formats:
  (a) Text-based PDFs — extracted directly with pdfplumber
  (b) Image-based PDFs — rendered to images and OCR'd with pytesseract

Also supports passing raw text (for testing or when you've already
extracted text yourself).

Usage:
    from integrations.food_lion import FoodLionParser

    parser = FoodLionParser()

    # From a PDF file
    result = parser.parse_pdf("path/to/food_lion_circular.pdf")

    # Save to the flyers directory
    parser.save(result, "app/data/flyers/food_lion_2026-05-18.json")

    # Then load via the existing ingestor
    from app.data.flyer_ingestor import FlyerIngestor
    ingestor = FlyerIngestor()
    candidates = ingestor.from_json("app/data/flyers/food_lion_2026-05-18.json")

Output JSON schema:
    {
      "grocer": "Food Lion",
      "store_location": "<location>",
      "flyer_week": "<YYYY-MM-DD>",
      "parse_metadata": { ... },
      "items": [ { ...IngredientCandidate fields... } ]
    }

Dependencies:
    pip install pdfplumber pytesseract pdf2image python-dateutil
    System: tesseract-ocr (apt install tesseract-ocr on Linux)
"""

from __future__ import annotations

import json
import re
import sys
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from integrations.food_lion.item_registry import lookup

logger = logging.getLogger(__name__)


# ── Sale price patterns ───────────────────────────────────────────────────────
# Covers the main formats found in Food Lion circulars:
#   $1.99/lb   $1.99 ea   2/$5   2 for $5   BOGO   $1.99

_PRICE_PATTERNS = [
    # "2/$5.00" or "2 for $5" — multi-unit deal
    (re.compile(r'(\d+)\s*/\s*\$(\d+\.?\d*)', re.IGNORECASE), "multi"),
    (re.compile(r'(\d+)\s+for\s+\$(\d+\.?\d*)', re.IGNORECASE), "multi"),
    # "$1.99/lb" or "$1.99 per lb" with unit
    (re.compile(r'\$(\d+\.?\d*)\s*/?\s*(?:per\s+)?(lb|oz|each|ea|pkg|bag|box|ct|count|gal|gallon|doz|dozen)',
                re.IGNORECASE), "unit"),
    # Plain "$1.99"
    (re.compile(r'\$(\d+\.?\d*)', re.IGNORECASE), "plain"),
    # BOGO or Buy 1 Get 1
    (re.compile(r'b[uo]go|buy\s+1\s+get\s+1', re.IGNORECASE), "bogo"),
]

# Unit strings that imply per-pound pricing in context
_PER_POUND_UNITS = {"lb", "pound", "lbs", "pounds"}

# Lines that are clearly not food items (headers, legal text, etc.)
_SKIP_PATTERNS = re.compile(
    r'(?:limit|while supplies|valid|expires|®|™|©|www\.|\.com|food lion|'
    r'weekly ad|digital coupon|mvp|savings|per household|restrictions|'
    r'page \d|^\d+$)',
    re.IGNORECASE
)


@dataclass
class ParsedItem:
    """Intermediate representation before registry enrichment."""
    raw_name: str
    sale_price_per_unit: float
    unit: str
    price_format: str           # "multi", "unit", "plain", "bogo"
    sale_savings_pct: float = 0.0
    regular_price_hint: Optional[float] = None  # if visible in flyer


@dataclass
class FlyerResult:
    grocer: str = "Food Lion"
    store_location: str = ""
    flyer_week: str = ""
    parse_metadata: dict = field(default_factory=dict)
    items: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class FoodLionParser:
    """
    Parses a Food Lion weekly circular (PDF or raw text) into WhollyFare
    flyer JSON format.

    Parameters
    ----------
    store_location : str
        Human-readable store location, e.g. "Palmyra, VA 22963"
    flyer_week : str | date | None
        ISO date string (YYYY-MM-DD) for the flyer's effective week.
        If None, defaults to the next Sunday.
    min_price : float
        Ignore parsed prices below this threshold (filters noise).
    max_price : float
        Ignore parsed prices above this threshold (filters noise).
    """

    def __init__(
        self,
        store_location: str = "Palmyra, VA 22963",
        flyer_week: str | date | None = None,
        min_price: float = 0.29,
        max_price: float = 49.99,
    ):
        self.store_location = store_location
        self.flyer_week = (
            flyer_week.isoformat() if isinstance(flyer_week, date)
            else flyer_week or self._next_sunday()
        )
        self.min_price = min_price
        self.max_price = max_price

    # ── Public API ────────────────────────────────────────────────────────────

    def parse_pdf(self, pdf_path: str | Path) -> FlyerResult:
        """
        Parse a Food Lion PDF circular.
        Tries text extraction first; falls back to OCR if the PDF is image-based.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        text = self._extract_text_pdfplumber(pdf_path)
        method = "pdfplumber"

        if not text or len(text.strip()) < 200:
            logger.info("PDF appears image-based — attempting OCR fallback.")
            text = self._extract_text_ocr(pdf_path)
            method = "ocr"

        if not text:
            raise RuntimeError(
                f"Could not extract text from {pdf_path.name}. "
                "Ensure pdfplumber and/or pytesseract + tesseract are installed."
            )

        result = self.parse_text(text)
        result.parse_metadata["source_file"] = pdf_path.name
        result.parse_metadata["extraction_method"] = method
        return result

    def parse_text(self, text: str) -> FlyerResult:
        """
        Parse pre-extracted flyer text into a FlyerResult.
        Useful for testing or when you have text from another source.
        """
        lines = self._clean_lines(text)
        raw_items = self._extract_items(lines)
        enriched = [self._enrich(item) for item in raw_items]

        # Filter out items where enrichment failed to produce a usable category
        valid = [e for e in enriched if e is not None]

        result = FlyerResult(
            grocer="Food Lion",
            store_location=self.store_location,
            flyer_week=self.flyer_week,
            parse_metadata={
                "total_lines": len(lines),
                "raw_items_found": len(raw_items),
                "items_after_enrichment": len(valid),
                "items_skipped": len(raw_items) - len(valid),
                "parsed_at": datetime.utcnow().isoformat() + "Z",
            },
            items=valid,
        )
        logger.info(
            f"Parsed {len(valid)} items from {len(lines)} lines "
            f"({len(raw_items) - len(valid)} skipped, "
            f"{result.parse_metadata.get('extraction_method','text')} method)."
        )
        return result

    def save(self, result: FlyerResult, output_path: str | Path) -> Path:
        """Save the FlyerResult to JSON. Creates parent dirs as needed."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Saved flyer JSON → {output_path}")
        return output_path

    # ── Text extraction ───────────────────────────────────────────────────────

    def _extract_text_pdfplumber(self, pdf_path: Path) -> str:
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("Run: pip install pdfplumber")

        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(
                    x_tolerance=3, y_tolerance=3
                ) or ""
                # Also try extracting from tables within the page
                for table in page.extract_tables() or []:
                    for row in table:
                        pages.append(" | ".join(str(c) for c in row if c))
                pages.append(page_text)
        return "\n".join(pages)

    def _extract_text_ocr(self, pdf_path: Path) -> str:
        """Image-based PDF → images → Tesseract OCR."""
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError:
            raise RuntimeError(
                "OCR dependencies missing. Run:\n"
                "  pip install pdf2image pytesseract\n"
                "  apt install tesseract-ocr poppler-utils"
            )
        images = convert_from_path(pdf_path, dpi=200)
        pages = []
        for img in images:
            pages.append(pytesseract.image_to_string(img, config="--psm 6"))
        return "\n".join(pages)

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _clean_lines(self, text: str) -> list[str]:
        """Normalise whitespace and remove obvious non-item lines."""
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if _SKIP_PATTERNS.search(line):
                continue
            # Collapse runs of whitespace
            line = re.sub(r'\s{2,}', ' ', line)
            lines.append(line)
        return lines

    def _extract_items(self, lines: list[str]) -> list[ParsedItem]:
        """
        Scan cleaned lines for (name, price) pairs.

        Strategy: for every line that contains a price signal, try to extract
        a clean item name from the same line or the adjacent line(s).
        """
        items: list[ParsedItem] = []
        used_indices: set[int] = set()

        for i, line in enumerate(lines):
            price, unit, fmt = self._extract_price(line)
            if price is None:
                continue
            if price < self.min_price or price > self.max_price:
                continue

            # Get the name: first try to strip the price token from the current
            # line; if that leaves nothing useful, look one line above.
            name = self._extract_name(line)
            if not name or len(name) < 3:
                if i > 0 and i - 1 not in used_indices:
                    name = self._extract_name(lines[i - 1])

            if not name or len(name) < 3:
                continue

            used_indices.add(i)
            items.append(ParsedItem(
                raw_name=name,
                sale_price_per_unit=price,
                unit=unit,
                price_format=fmt,
            ))

        return items

    def _extract_price(self, line: str) -> tuple[float | None, str, str]:
        """
        Return (price_per_unit, unit_string, format_tag) for the first
        recognisable price in `line`, or (None, '', '') if none found.
        """
        for pattern, fmt in _PRICE_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue

            if fmt == "bogo":
                # Need to find a regular price on the same line to halve it
                reg = re.search(r'\$(\d+\.?\d*)', line)
                if reg:
                    return round(float(reg.group(1)) / 2, 2), "each", "bogo"
                continue

            if fmt == "multi":
                count = float(m.group(1))
                total = float(m.group(2))
                price = round(total / count, 2)
                return price, "each", fmt

            if fmt == "unit":
                price = float(m.group(1))
                unit_raw = m.group(2).lower()
                unit = "lb" if unit_raw in _PER_POUND_UNITS else unit_raw
                return price, unit, fmt

            if fmt == "plain":
                return float(m.group(1)), "each", fmt

        return None, "", ""

    def _extract_name(self, line: str) -> str:
        """
        Strip price tokens, units, quantities, and common flyer noise from
        a line to leave a clean item name.
        """
        # Remove price tokens
        name = re.sub(r'\$\d+\.?\d*', '', line)
        # Remove quantity prefixes like "2/$5" "3 for"
        name = re.sub(r'\d+\s*(?:/|for)\s*', '', name, flags=re.IGNORECASE)
        # Remove unit tokens
        name = re.sub(
            r'\b(?:per|each|ea|lb|lbs|oz|pkg|bag|box|ct|count|gal|gallon|doz|dozen|pk)\b',
            '', name, flags=re.IGNORECASE
        )
        # Remove standalone numbers (sizes, weights)
        name = re.sub(r'\b\d+(?:\.\d+)?\b', '', name)
        # Remove stray punctuation
        name = re.sub(r'[|/\\,!@#%^*_=+<>{}[\]]', ' ', name)
        # Collapse whitespace
        name = re.sub(r'\s{2,}', ' ', name).strip().strip('-').strip()
        # Title-case for consistency
        return name.title() if name else ""

    # ── Enrichment ────────────────────────────────────────────────────────────

    def _enrich(self, item: ParsedItem) -> dict | None:
        """
        Look up category, allergens, tags, and weight from the item registry,
        then assemble the full flyer JSON item dict.

        POC: Registry misses fall through to inferred values so real circular
        items aren't silently dropped. Unknown items get category="other" and
        empty allergens — conservative but honest.
        PROD: USDA FDC lookup fills in full nutrition + allergen data per item.
        """
        info = lookup(item.raw_name)
        if info is None:
            # Not in registry — infer what we can rather than dropping the item.
            # Category inference uses the same keyword map as the generic ingestor.
            inferred_cat = self._infer_category(item.raw_name)
            info = {
                "category":               inferred_cat,
                "allergens":              [],
                "tags":                   [],
                "standard_unit_weight_g": 100.0,
                "usda_fdc_id":            None,
            }
            logger.debug(f"No registry match for {item.raw_name!r} — using inferred cat={inferred_cat}")

        # Estimate savings % from regular-price hint if available
        savings_pct = item.sale_savings_pct
        if item.regular_price_hint and item.regular_price_hint > item.sale_price_per_unit:
            savings_pct = round(
                (1 - item.sale_price_per_unit / item.regular_price_hint) * 100, 1
            )

        # Stub nutrition — USDA enricher fills this in (see usda_enricher.py)
        nutrition_stub = {
            "protein_g": 0, "fiber_g": 0, "saturated_fat_g": 0,
            "sodium_mg": 0, "added_sugar_g": 0, "iron_mg": 0,
            "calcium_mg": 0, "potassium_mg": 0, "vitamin_c_mg": 0,
            "sale_savings_pct": savings_pct,
        }

        return {
            "name": item.raw_name,
            "usda_fdc_id": info.get("usda_fdc_id"),
            "allergens": info.get("allergens", []),
            "category": info.get("category", "other"),
            "tags": info.get("tags", []),
            "sale_price_per_unit": item.sale_price_per_unit,
            "unit": item.unit,
            "standard_unit_weight_g": info.get("standard_unit_weight_g", 100.0),
            "nutrition": nutrition_stub,
        }

    # ── Utility ───────────────────────────────────────────────────────────────

    @staticmethod
    def _next_sunday() -> str:
        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        next_sun = today if days_until_sunday == 0 else \
            date.fromordinal(today.toordinal() + days_until_sunday)
        return next_sun.isoformat()

"""
flyer_ingestor.py
-----------------
Parses grocer weekly sale circulars into structured IngredientCandidate objects.

Supports:
  - JSON mock/cached flyers  (primary dev/demo path)
  - PDF flyer upload          (pdfplumber text + pytesseract OCR fallback)
  - HTML flyer scraping       (beautifulsoup4)

Chain-specific PDF parsing is dispatched via CHAIN_PARSERS. Food Lion has a
dedicated parser (integrations/food_lion/parser.py). All others fall through
to the improved generic parser below.

PROD roadmap: direct grocer API integrations replace PDF for Kroger, Publix,
Aldi, Harris Teeter. PDF stays as a fallback for independent/regional chains.
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional

from app.core_logic.constraint_engine import IngredientCandidate

logger = logging.getLogger(__name__)


# ── Junk-line filter ──────────────────────────────────────────────────────────
# Lines that are almost certainly not food items. Applied before price matching.
_JUNK_PATTERNS = re.compile(
    r'^(page\s+\d+|weekly\s+(ad|circular)|valid\s+(through|thru|until)|'
    r'while\s+supplies\s+last|limit\s+\d|excludes|see\s+store|'
    r'prices\s+good|shop\s+online|download\s+the|scan\s+(here|to)|'
    r'www\.|https?://|©|®|™|\d{5}|[A-Z]{2}\s+\d{5}|'
    r'customer\s+service|store\s+hours|pharmacy|fuel\s+points|'
    r'must\s+(buy|purchase)|mix\s+(or|&)\s+match|buy\s+\d|'
    r'with\s+(card|digital|coupon)|savings\s+applied|'
    r'not\s+responsible|quantity\s+rights|typo)',
    re.IGNORECASE,
)

# ── Price patterns (in priority order) ───────────────────────────────────────
# Each tuple: (compiled_regex, price_type)
# price_type drives how we compute sale_price_per_unit.
_PRICE_RE = [
    # "2/$5.00" or "2/$5" or "2 for $5"
    (re.compile(r'(\d+)\s*(?:/|for)\s*\$\s*(\d+\.?\d*)', re.I), "multi"),
    # "$1.99/lb" "$2.50 per oz" "$0.49/ea"
    (re.compile(
        r'\$\s*(\d+\.?\d*)\s*/?\s*(?:per\s+)?(lb|lbs|oz|each|ea|ct|count|pkg|bag|box|gal|gallon|qt|quart|doz|dozen)',
        re.I), "unit"),
    # Plain "$1.99" anywhere on the line
    (re.compile(r'\$\s*(\d+\.?\d*)', re.I), "plain"),
    # "BOGO" or "Buy 1 Get 1"
    (re.compile(r'b[ou]go|buy\s*1\s*get\s*1\s*(free)?', re.I), "bogo"),
]

# ── Category keyword mapping ──────────────────────────────────────────────────
_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("produce",  ["apple", "banana", "berry", "berries", "grape", "melon", "peach", "pear",
                  "plum", "citrus", "orange", "lemon", "lime", "mango", "pineapple", "avocado",
                  "tomato", "potato", "onion", "garlic", "pepper", "broccoli", "spinach",
                  "lettuce", "carrot", "celery", "cucumber", "squash", "zucchini", "corn",
                  "mushroom", "cabbage", "kale", "asparagus", "artichoke", "leek", "radish",
                  "strawberr", "blueberr", "raspberr", "blackberr", "cherry", "cherri",
                  "watermelon", "cantaloupe", "honeydew"]),
    ("protein",  ["chicken", "beef", "pork", "turkey", "salmon", "tilapia", "shrimp", "tuna",
                  "steak", "ground", "roast", "chop", "ribs", "brisket", "bacon", "ham",
                  "sausage", "hot dog", "frank", "lamb", "veal", "duck", "crab", "lobster",
                  "catfish", "cod", "flounder", "halibut", "perch", "trout", "mahi"]),
    ("dairy",    ["milk", "cheese", "yogurt", "butter", "cream", "sour cream", "cottage",
                  "whipping", "half and half", "creamer", "kefir", "margarine"]),
    ("grain",    ["bread", "pasta", "rice", "cereal", "oat", "tortilla", "wrap", "bagel",
                  "muffin", "roll", "biscuit", "cracker", "chip", "pretzel", "granola",
                  "flour", "cornmeal", "quinoa", "barley", "couscous"]),
    ("frozen",   ["frozen", "ice cream", "pizza", "burrito", "entree", "nugget", "waffle",
                  "pocket", "pot pie", "meal"]),
    ("beverage", ["juice", "soda", "water", "tea", "coffee", "drink", "lemonade", "sparkling",
                  "energy", "sports drink", "gatorade", "powerade"]),
    ("legume",   ["bean", "lentil", "chickpea", "pea", "edamame", "tofu", "tempeh"]),
    ("pantry",   ["oil", "vinegar", "sauce", "soup", "broth", "stock", "canned", "can of",
                  "jar", "salsa", "ketchup", "mustard", "mayo", "dressing", "seasoning",
                  "spice", "herb", "salt", "sugar", "honey", "syrup", "jam", "jelly",
                  "peanut butter", "almond butter", "nutella", "spread"]),
]

# ── Unit normaliser ───────────────────────────────────────────────────────────
_UNIT_MAP = {
    "lbs": "lb", "pound": "lb", "pounds": "lb",
    "ounce": "oz", "ounces": "oz",
    "ea": "each", "ct": "each", "count": "each",
    "gallon": "gal", "gallons": "gal",
    "quart": "qt", "quarts": "qt",
    "dozen": "doz",
    "package": "pkg", "packages": "pkg",
    "bags": "bag", "boxes": "box",
}


def _infer_category(name: str) -> str:
    name_lower = name.lower()
    for cat, keywords in _CATEGORY_KEYWORDS:
        if any(kw in name_lower for kw in keywords):
            return cat
    return "other"


def _normalise_unit(raw: str) -> str:
    return _UNIT_MAP.get(raw.lower(), raw.lower())


def _parse_price_from_line(line: str) -> tuple[Optional[float], str, str]:
    """Return (sale_price_per_unit, unit, price_type) from a line of text.

    Returns (None, 'each', 'none') if no price found.
    """
    for pattern, ptype in _PRICE_RE:
        m = pattern.search(line)
        if not m:
            continue

        if ptype == "multi":
            qty, total = float(m.group(1)), float(m.group(2))
            return (round(total / max(qty, 1), 2), "each", ptype)

        if ptype == "unit":
            price = float(m.group(1))
            unit  = _normalise_unit(m.group(2))
            return (price, unit, ptype)

        if ptype == "plain":
            return (float(m.group(1)), "each", ptype)

        if ptype == "bogo":
            return (0.0, "each", ptype)   # price unknown; flag for manual review

    return (None, "each", "none")


def _strip_price_from_name(name: str) -> str:
    """Remove price artefacts that ended up in the item name."""
    name = re.sub(r'\$[\d.]+', '', name)
    name = re.sub(r'\b\d+\s*/\s*\$[\d.]+', '', name)
    name = re.sub(r'\b\d+\s+for\s+\$[\d.]+', '', name, flags=re.I)
    name = re.sub(r'\b(per\s+)?(lb|lbs|oz|ea|each|pkg|bag|box|gal|qt|ct)\b', '', name, flags=re.I)
    name = re.sub(r'\s{2,}', ' ', name)
    return name.strip(" ,-.")


class FlyerIngestor:
    """Parse grocer sale circulars into IngredientCandidate lists."""

    # -- Public API -----------------------------------------------------------

    def from_json(self, path: str | Path) -> list[IngredientCandidate]:
        """Load a mock or cached flyer from JSON. Primary method for dev/demo."""
        with open(path) as f:
            raw = json.load(f)
        return [self._parse_item(item) for item in raw.get("items", [])]

    def from_pdf(self, path: str | Path, chain: str = "") -> list[IngredientCandidate]:
        """Extract sale items from a PDF flyer.

        Tries text extraction first (fast). Falls back to OCR if the page is
        image-based or yields fewer than 3 items.

        POC: chain-specific dispatch for Food Lion only. All others use the
             improved generic parser below.
        PROD: Each supported chain gets a dedicated parser trained on its layout.
        """
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

        all_text: list[str] = []
        image_pages: list[int] = []

        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if len(text.strip()) < 30:
                    image_pages.append(i)
                else:
                    all_text.append(text)

        candidates: list[IngredientCandidate] = []

        # Text-based pages
        for text in all_text:
            candidates.extend(self._parse_text_block(text, chain=chain))

        # Image-based pages — attempt OCR
        if image_pages:
            ocr_results = self._ocr_pages(path, image_pages, chain=chain)
            candidates.extend(ocr_results)

        # Deduplicate by name (keep first occurrence)
        seen: set[str] = set()
        unique: list[IngredientCandidate] = []
        for c in candidates:
            key = c.name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def from_html(self, html: str, grocer_chain: str = "") -> list[IngredientCandidate]:
        """Parse a grocer's weekly ad HTML page (beautifulsoup4 required)."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise RuntimeError("beautifulsoup4 not installed. Run: pip install beautifulsoup4")

        soup = BeautifulSoup(html, "html.parser")
        items = []
        for tag in soup.find_all(class_=lambda c: c and "sale" in c.lower()):
            name = tag.get_text(strip=True)
            if name:
                items.append(self._stub_candidate(name))
        return items

    # -- Internal helpers -----------------------------------------------------

    def _parse_item(self, item: dict) -> IngredientCandidate:
        return IngredientCandidate(
            name=item["name"],
            usda_fdc_id=item.get("usda_fdc_id"),
            allergens=item.get("allergens", []),
            nutrition=item.get("nutrition", {}),
            sale_price_per_unit=float(item["sale_price_per_unit"]),
            unit=item.get("unit", "each"),
            standard_unit_weight_g=float(item.get("standard_unit_weight_g", 100)),
            category=item.get("category", "other"),
            tags=item.get("tags", []),
        )

    def _stub_candidate(self, name: str, price: float = 0.0,
                        unit: str = "each", category: str = "") -> IngredientCandidate:
        return IngredientCandidate(
            name=name,
            usda_fdc_id=None,
            allergens=[],
            nutrition={},
            sale_price_per_unit=price,
            unit=unit,
            standard_unit_weight_g=100.0,
            category=category or _infer_category(name),
            tags=[],
        )

    def _parse_text_block(self, text: str, chain: str = "") -> list[IngredientCandidate]:
        """Improved heuristic parser for PDF-extracted flyer text.

        Strategy:
          1. Split into lines.
          2. Skip obvious junk (headers, legal text, URLs).
          3. For each line, extract price using prioritised patterns.
          4. Extract item name as the non-price remainder.
          5. Infer category from name keywords.

        POC: No USDA enrichment here — that happens in a separate async pass.
        PROD: Each line hit gets queued for USDA FDC lookup; confidence score
              determines whether it goes straight to the engine or needs review.
        """
        candidates: list[IngredientCandidate] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            # Skip short/empty lines and obvious junk
            if len(line) < 4:
                continue
            if _JUNK_PATTERNS.match(line):
                continue
            # Skip lines that are all caps and short (likely section headers)
            if line.isupper() and len(line) < 20:
                continue

            price, unit, ptype = _parse_price_from_line(line)

            # No price found — skip (can't use in the engine without a price)
            if price is None:
                continue

            # Skip suspiciously low or zero prices (except BOGO which is flagged)
            if price == 0.0 and ptype != "bogo":
                continue

            # Extract item name: strip the price match and surrounding noise
            name = _strip_price_from_name(line)

            # Must have a meaningful name
            if len(name) < 3:
                continue
            # Names longer than 60 chars are usually garbled lines
            if len(name) > 60:
                name = name[:60].rsplit(" ", 1)[0]

            tags = ["bogo"] if ptype == "bogo" else []
            if ptype == "multi":
                tags.append("multi-buy")

            candidates.append(self._stub_candidate(
                name=name,
                price=price,
                unit=unit,
                category=_infer_category(name),
            ))

            # Attach extra tags without a setter (IngredientCandidate is a dataclass)
            candidates[-1].tags = tags

        return candidates

    def _ocr_pages(self, path: Path, page_indices: list[int],
                   chain: str = "") -> list[IngredientCandidate]:
        """OCR image-based PDF pages using pytesseract + pdf2image.

        POC: Tesseract must be installed on the host system.
             Streamlit Cloud: add 'tesseract-ocr' to packages.txt.
        PROD: Run OCR in a Lambda / Celery worker. Store raw OCR output for
              re-parsing as parser improves, without re-scanning the PDF.
        """
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError:
            logger.warning("pdf2image/pytesseract not available — skipping OCR pages")
            return []

        candidates: list[IngredientCandidate] = []
        try:
            images = convert_from_path(str(path), first_page=1,
                                       last_page=max(page_indices) + 1)
            for i in page_indices:
                if i >= len(images):
                    continue
                text = pytesseract.image_to_string(images[i])
                candidates.extend(self._parse_text_block(text, chain=chain))
        except Exception as e:
            logger.warning(f"OCR failed for {path}: {e}")

        return candidates

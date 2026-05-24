"""
claude_extractor.py
-------------------
Converts a grocer weekly-circular PDF into IngredientCandidate objects using
Claude's vision API.

How it works
~~~~~~~~~~~~
1. Render each PDF page to a PNG image at 150 DPI using pdftoppm.
2. Base64-encode each image and send it to claude-3-5-haiku (fast, cheap).
3. Claude reads the sale price, item name, unit, and category from the image.
4. We parse Claude's JSON response into IngredientCandidate objects.
5. Caller gets back a list[IngredientCandidate] ready to merge into flyer_data.

Pilot vs. Production
--------------------
Pilot:  Tim uploads PDFs manually in the Admin page. We process synchronously.
        One API call per page (parallelism not needed at pilot scale).
        Temp PNG files are cleaned up after extraction.
PROD:   Background job queue. Store per-store circular in S3/Supabase Storage.
        Diff against prior week to detect new/expired deals.
        Confidence scoring per item; human review queue for low-confidence extractions.

Dependencies
~~~~~~~~~~~~
  pip install anthropic>=0.25.0
  apt-get install poppler-utils    (provides pdftoppm; packages.txt for Streamlit Cloud)

Environment
~~~~~~~~~~~
  ANTHROPIC_API_KEY  — required. Set in .env or Streamlit secrets.
"""

import base64
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from app.core_logic.constraint_engine import IngredientCandidate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------
_MODEL        = "claude-haiku-4-5-20251001"    # current Haiku model (3-haiku-20240307 deprecated May 2026)
_MAX_TOKENS   = 2048
_MAX_PAGES    = 20          # safety cap — most circulars are 8–16 pages
_DPI          = 72          # 72 DPI is enough for Claude to read sale prices
_MAX_PX_WIDTH = 2048        # cap pixel width so images stay under Claude 5 MB limit

# ---------------------------------------------------------------------------
# The extraction prompt
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = (
    "You are a grocery circular data extractor. Your job is to read scanned "
    "weekly-ad images and extract every item that has a sale price. "
    "Return ONLY valid JSON — no markdown, no prose, no code fences."
)

_USER_PROMPT = """Extract every sale item visible on this grocery circular page.

Return a JSON array. Each element must have these exact keys:
  "name"       – item name as printed (e.g. "Boneless Skinless Chicken Breast")
  "price"      – sale price as a float (e.g. 2.99). For multi-buy deals like
                 "2/$5" compute per-unit price (2.50). For BOGO, use half the
                 regular price if shown, otherwise use 0.
  "unit"       – unit string: "lb", "oz", "each", "dozen", "gallon", "pkg", etc.
  "multi_buy"  – integer quantity if this is a multi-buy deal (e.g. 2 for "2/$5"),
                 otherwise 1.
  "category"   – one of: "produce", "protein", "dairy", "deli", "grain",
                 "frozen", "snack", "beverage", "household", "personal_care", "other"
  "raw_text"   – the raw price/quantity text exactly as printed (e.g. "2/$5.00")

Rules:
- Include every item with a visible sale price.
- Skip store-brand logos, legal text, store hours, coupons that are not product prices.
- If the price unit is ambiguous, default to "each".
- If no items are visible (e.g. cover page, map), return an empty array [].

Return only the JSON array, nothing else."""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ExtractionResult:
    """Returned by extract_pdf(). Includes items AND a per-page log."""

    def __init__(self):
        self.candidates: list[IngredientCandidate] = []
        self.raw_items:  list[dict] = []           # raw dicts before conversion
        self.page_log:   list[dict] = []           # {page, item_count, error?}
        self.errors:     list[str]  = []

    @property
    def item_count(self) -> int:
        return len(self.candidates)

    @property
    def success(self) -> bool:
        return self.item_count > 0


def extract_pdf(
    pdf_path: str | Path,
    store_chain: str = "unknown",
    api_key: Optional[str] = None,
    max_pages: int = _MAX_PAGES,
) -> ExtractionResult:
    """
    Full pipeline: PDF → PNG pages → Claude Vision → IngredientCandidates.

    Args:
        pdf_path:    Path to the PDF file.
        store_chain: e.g. "Food Lion" — embedded in candidate metadata.
        api_key:     Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        max_pages:   Safety cap on pages processed (default 20).

    Returns:
        ExtractionResult with .candidates, .raw_items, .page_log, .errors.
    """
    result = ExtractionResult()
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        result.errors.append(f"PDF not found: {pdf_path}")
        return result

    key = api_key or os.environ.get("ANTHROPIC_API_KEY") or _get_streamlit_secret()
    if not key:
        result.errors.append(
            "ANTHROPIC_API_KEY not set. Add it to .env or Streamlit secrets."
        )
        return result

    # Render PDF → PNGs in a temp directory
    with tempfile.TemporaryDirectory(prefix="wf_extract_") as tmpdir:
        png_paths = _render_pdf_to_pngs(pdf_path, tmpdir, max_pages, result)
        if not png_paths:
            if not result.errors:
                result.errors.append("No pages could be rendered from PDF.")
            return result

        # Extract items from each page
        for page_num, png_path in enumerate(png_paths, start=1):
            _extract_page(png_path, page_num, store_chain, key, result)

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_pdf_to_pngs(
    pdf_path: Path,
    output_dir: str,
    max_pages: int,
    result: ExtractionResult,
) -> list[Path]:
    """
    Render PDF pages to PNG files using PyMuPDF (fitz).
    Pure Python — no system poppler/pdftoppm required.
    Falls back to pdftoppm if fitz is not installed.
    Returns list of PNG paths in page order.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        result.errors.append(
            "PyMuPDF not installed. Run: pip install pymupdf>=1.23.0"
        )
        return []

    output_dir = Path(output_dir)
    jpg_paths = []

    try:
        doc = fitz.open(str(pdf_path))
        page_count = min(len(doc), max_pages)

        for i in range(page_count):
            page = doc.load_page(i)

            # Scale so the longest edge is at most _MAX_PX_WIDTH pixels.
            # Food Lion / Giant PDFs can be 7000+ pts wide — rendering at 1:1
            # produces 20+ MB PNGs that Claude rejects. JPEG at 80% quality
            # keeps files well under the 5 MB API limit.
            page_w = page.rect.width   # points
            page_h = page.rect.height  # points
            longest = max(page_w, page_h)
            zoom = min(_DPI / 72.0, _MAX_PX_WIDTH / longest)
            mat = fitz.Matrix(zoom, zoom)

            pix = page.get_pixmap(matrix=mat, alpha=False)
            jpg_bytes = pix.tobytes("jpeg", jpg_quality=80)

            # Safety net: if still over 4 MB, halve dimensions and re-encode
            if len(jpg_bytes) > 4 * 1024 * 1024:
                zoom2 = zoom * 0.5
                mat2 = fitz.Matrix(zoom2, zoom2)
                pix = page.get_pixmap(matrix=mat2, alpha=False)
                jpg_bytes = pix.tobytes("jpeg", jpg_quality=75)

            out_path = output_dir / f"page-{i+1:04d}.jpg"
            out_path.write_bytes(jpg_bytes)
            jpg_paths.append(out_path)
            logger.debug("Rendered page %d/%d  %.1f KB", i + 1, page_count,
                         len(jpg_bytes) / 1024)

        doc.close()
    except Exception as exc:
        result.errors.append(f"PDF render error: {exc}")
        return []

    return jpg_paths


def _extract_page(
    png_path: Path,
    page_num: int,
    store_chain: str,
    api_key: str,
    result: ExtractionResult,
) -> None:
    """Send one PNG page to Claude and append parsed items to result."""
    try:
        import anthropic
    except ImportError:
        result.errors.append(
            "anthropic package not installed. Run: pip install anthropic>=0.25.0"
        )
        return

    # Read and encode the image
    image_data = base64.standard_b64encode(png_path.read_bytes()).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type":       "image",
                            "source": {
                                "type":       "base64",
                                "media_type": "image/jpeg",
                                "data":       image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": _USER_PROMPT,
                        },
                    ],
                }
            ],
        )
    except Exception as exc:
        err = f"Claude API error on page {page_num}: {exc}"
        logger.error(err)
        result.errors.append(err)
        result.page_log.append({"page": page_num, "item_count": 0, "error": str(exc)})
        return

    raw_text = message.content[0].text.strip()
    items = _parse_json_response(raw_text, page_num, result)

    for item in items:
        candidate = _dict_to_candidate(item, store_chain)
        if candidate:
            result.candidates.append(candidate)
            result.raw_items.append(item)

    result.page_log.append({"page": page_num, "item_count": len(items)})
    logger.info("Page %d: extracted %d items", page_num, len(items))


def _parse_json_response(text: str, page_num: int, result: ExtractionResult) -> list[dict]:
    """Parse Claude's JSON response, tolerating minor formatting issues."""
    # Strip any accidental markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()

    if not text or text == "[]":
        return []

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        # Claude occasionally wraps in {"items": [...]}
        if isinstance(data, dict):
            for key in ("items", "products", "results", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
    except json.JSONDecodeError as exc:
        err = f"JSON parse error on page {page_num}: {exc}"
        logger.warning(err)
        result.errors.append(err)

    return []


def _dict_to_candidate(item: dict, store_chain: str) -> Optional[IngredientCandidate]:
    """Convert a raw dict from Claude into an IngredientCandidate."""
    try:
        name = str(item.get("name", "")).strip()
        if not name:
            return None

        price = float(item.get("price", 0.0) or 0.0)
        unit  = str(item.get("unit", "each")).strip() or "each"
        cat   = str(item.get("category", "other")).strip()
        multi = int(item.get("multi_buy", 1) or 1)

        # For multi-buy, Claude should already have computed per-unit, but double-check
        if multi > 1 and price > 0:
            price = round(price / multi, 2)  # ensure per-unit

        # Map Claude's categories to WhollyFare categories
        _cat_map = {
            "produce":       "produce",
            "protein":       "protein",
            "dairy":         "dairy",
            "deli":          "protein",
            "grain":         "grain",
            "frozen":        "frozen",
            "snack":         "snack",
            "beverage":      "beverage",
            "household":     "household",
            "personal_care": "personal_care",
            "other":         "other",
        }
        wf_category = _cat_map.get(cat.lower(), "other")

        return IngredientCandidate(
            name=name,
            usda_fdc_id=None,                    # PROD: look up via USDA FoodData API
            allergens=[],                        # PROD: derive from ingredient list
            nutrition={},                        # PROD: fetch from USDA
            sale_price_per_unit=price,
            unit=unit,
            standard_unit_weight_g=0.0,          # PROD: lookup
            category=wf_category,
            tags=[store_chain.lower().replace(" ", "_")],  # tag with source store
        )
    except Exception as exc:
        logger.warning("Could not convert item to candidate: %s — %s", item, exc)
        return None


def _get_streamlit_secret() -> Optional[str]:
    """Try to read ANTHROPIC_API_KEY from Streamlit secrets (non-crashing)."""
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Convenience: extract from raw bytes (for Streamlit file_uploader)
# ---------------------------------------------------------------------------

def extract_uploaded_pdf(
    file_bytes: bytes,
    store_chain: str = "unknown",
    api_key: Optional[str] = None,
    max_pages: int = _MAX_PAGES,
) -> ExtractionResult:
    """
    Like extract_pdf() but accepts raw bytes from st.file_uploader.
    Writes to a temp file then delegates to extract_pdf().
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        return extract_pdf(tmp_path, store_chain, api_key, max_pages)
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Merge extracted items into flyer_data session dict
# ---------------------------------------------------------------------------

def merge_into_flyer_data(
    result: ExtractionResult,
    store_key: str,
    flyer_data: dict,
) -> dict:
    """
    Merge extraction result candidates into the session flyer_data dict.
    Returns the updated flyer_data.
    POC: Simple merge by store key. PROD: deduplicate by UPC/name.
    """
    if not result.candidates:
        return flyer_data
    existing = flyer_data.get(store_key, [])
    existing_names = {
        (c.name if hasattr(c, 'name') else c.get('name', '')).lower()
        for c in existing
    }
    for cand in result.candidates:
        name = cand.name if hasattr(cand, 'name') else cand.get('name', '')
        if name.lower() not in existing_names:
            existing.append(cand)
            existing_names.add(name.lower())
    flyer_data[store_key] = existing
    return flyer_data

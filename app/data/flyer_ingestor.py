"""
flyer_ingestor.py
-----------------
Parses grocer weekly sale circulars into structured IngredientCandidate objects.

MVP supports:
  - JSON mock flyers (for development/testing)
  - PDF flyer upload (via pdfplumber)
  - HTML flyer scraping (via BeautifulSoup4)

v2 roadmap: direct grocer API integrations (Kroger, Publix, Aldi, etc.)
"""

import json
from pathlib import Path
from typing import Optional
from app.core_logic.constraint_engine import IngredientCandidate


class FlyerIngestor:

    def from_json(self, path: str | Path) -> list[IngredientCandidate]:
        """Load a mock or cached flyer from JSON. Primary method for MVP dev."""
        with open(path) as f:
            raw = json.load(f)
        return [self._parse_item(item) for item in raw.get("items", [])]

    def from_pdf(self, path: str | Path) -> list[IngredientCandidate]:
        """
        Extract sale items from a PDF flyer.
        Requires: pip install pdfplumber
        """
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

        candidates = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                candidates.extend(self._parse_text_block(text))
        return candidates

    def from_html(self, html: str, grocer_chain: str) -> list[IngredientCandidate]:
        """
        Parse a grocer's weekly ad HTML page.
        Requires: pip install beautifulsoup4
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise RuntimeError("beautifulsoup4 not installed. Run: pip install beautifulsoup4")

        soup = BeautifulSoup(html, "html.parser")
        # Chain-specific parsing logic goes here (v2: one parser per chain)
        # MVP: generic heuristic — look for price + item name patterns
        items = []
        for tag in soup.find_all(class_=lambda c: c and "sale" in c.lower()):
            name = tag.get_text(strip=True)
            if name:
                items.append(self._stub_candidate(name))
        return items

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

    def _stub_candidate(self, name: str) -> IngredientCandidate:
        """Minimal stub for HTML-scraped items pending USDA enrichment."""
        return IngredientCandidate(
            name=name,
            usda_fdc_id=None,
            allergens=[],
            nutrition={},
            sale_price_per_unit=0.0,
            unit="each",
            standard_unit_weight_g=100.0,
            category="other",
            tags=[],
        )

    def _parse_text_block(self, text: str) -> list[IngredientCandidate]:
        """
        Heuristic text parser for PDF-extracted flyer text.
        MVP: returns stubs; USDA enrichment happens downstream.
        """
        import re
        candidates = []
        # Look for lines like "$1.99 Chicken Breast" or "Apples $0.79/lb"
        pattern = re.compile(r'\$(\d+\.\d{2})\s+(.+?)(?:\n|$)|(.+?)\s+\$(\d+\.\d{2})')
        for match in pattern.finditer(text):
            if match.group(1):
                price, name = float(match.group(1)), match.group(2).strip()
            else:
                name, price = match.group(3).strip(), float(match.group(4))
            if len(name) > 2:
                stub = self._stub_candidate(name)
                stub.sale_price_per_unit = price
                candidates.append(stub)
        return candidates

"""
data — Ingredient and price ingestion layer.

Parses local grocer flyers (JSON / PDF / HTML) into IngredientCandidate
objects that the core_logic package can score and plan against.
"""

from .flyer_ingestor import FlyerIngestor

__all__ = ["FlyerIngestor"]

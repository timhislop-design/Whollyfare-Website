# Food Lion Flyer Parser

Converts a Food Lion weekly circular PDF into WhollyFare flyer JSON.

---

## Weekly workflow (every Sunday)

### 1. Download the flyer PDF

Go to https://stores.foodlion.com and download the current weekly circular PDF
for your store (Palmyra, VA). Save it anywhere convenient.

### 2. Parse the flyer

```bash
# From the repo root
python -m integrations.food_lion.cli \
  --pdf "/path/to/food_lion_circular.pdf" \
  --location "Palmyra, VA 22963" \
  --week "2026-05-18" \
  --out "app/data/flyers/food_lion_2026-05-18.json"
```

Or from Python:

```python
from integrations.food_lion import FoodLionParser
from integrations.food_lion.usda_enricher import USDAEnricher

parser = FoodLionParser(
    store_location="Palmyra, VA 22963",
    flyer_week="2026-05-18",
)
result = parser.parse_pdf("food_lion_circular.pdf")

# Enrich with real nutrition data (requires free USDA API key)
enricher = USDAEnricher(api_key="YOUR_KEY")
enricher.enrich(result)

parser.save(result, "app/data/flyers/food_lion_2026-05-18.json")
```

### 3. Load in the app

The output JSON is read by the existing `FlyerIngestor.from_json()`:

```python
from app.data.flyer_ingestor import FlyerIngestor
ingestor = FlyerIngestor()
candidates = ingestor.from_json("app/data/flyers/food_lion_2026-05-18.json")
```

---

## Getting a USDA API Key (free, 2 minutes)

1. Go to https://api.data.gov/signup/
2. Fill in your name and email
3. Key arrives by email immediately
4. Set it: `export USDA_API_KEY=your_key_here`

Without the key, items parse fine but nutrition fields stay as zeros.
The constraint engine still works — it just can't score nutrition quality
until the key is set.

---

## How the parser works

```
PDF → pdfplumber text extraction
         ↓ (fallback if image-based PDF)
     pytesseract OCR
         ↓
     line cleaning (remove headers, legal text, page numbers)
         ↓
     price pattern matching (handles $X.XX/lb, 2/$5, BOGO, etc.)
         ↓
     name extraction (strip price tokens, clean up)
         ↓
     item registry lookup (assigns category, allergens, tags, weight)
         ↓
     USDA enricher (fills in nutrition per 100g)
         ↓
     flyer JSON (same format as sample_flyer.json)
```

## What gets parsed vs. skipped

**Parsed:** Proteins, produce, grains, legumes, dairy, oils — anything matching
the item registry (~80 common grocery item patterns).

**Skipped:** Non-food items, household goods, beverages, snacks, prepared foods,
brand-specific items with no registry match. These appear in `parse_metadata.items_skipped`.

**Adding new items:** Edit `item_registry.py` and add a new entry under the
appropriate category. The key is a lowercase name fragment; the longer/more
specific it is, the higher priority it gets.

---

## Troubleshooting

**"PDF appears image-based"** — Install OCR dependencies:
```bash
pip install pdf2image pytesseract
apt install tesseract-ocr poppler-utils   # Linux
brew install tesseract poppler            # macOS
```

**Low item count** — The PDF may use unusual formatting. Check `parse_metadata.items_skipped`
and add the missed item names to `item_registry.py`.

**Prices look wrong** — Food Lion sometimes uses a non-standard price format.
Open an issue with the raw PDF text and we'll add a new price pattern.

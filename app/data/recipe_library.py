"""recipe_library.py — WhollyFare® Recipe Library

150 original recipes across 5 cuisine types, structured for the meal planner engine.
Each recipe is tagged with protein type, dietary flags, complexity, and ingredient data
that distinguishes pantry staples from items that need to be purchased.

POC note: This library is handcrafted for pilot quality and legal cleanliness.
Phase 2 expansion strategy: identify the most-commented, highest-rated community
recipe variants across Allrecipes, Reddit r/cooking, and similar platforms — take
the crowd-validated ingredient improvements (ingredient lists are not copyrightable),
rename for WhollyFare branding, add to library. Result: recipes that reflect how
households actually cook, not how test kitchens photograph.

Phase 3: replace/supplement with Spoonacular or Edamam API once at 50+ households.

Ingredient categories:
  protein     — primary protein (drives sale matching)
  produce     — fresh vegetables, fruit
  grain       — pasta, rice, tortillas, bread
  dairy       — cheese, cream, butter, eggs
  canned      — canned tomatoes, beans, broth, coconut milk
  pantry      — oils, vinegar, soy sauce, hot sauce
  spice       — dried spices and herbs (always pantry_stable)

pantry_stable=True  — assume household already has it; don't add to shopping list
pantry_stable=False — must be purchased for this recipe
"""

from typing import Optional

# ── Recipe Data ────────────────────────────────────────────────────────────────

def _r(id, name, cuisine, protein, ingredients, serves, minutes, complexity,
       gf=False, df=False, nut_free=True, veg=False, vegan=False, low_carb=False,
       tags=None):
    """Compact recipe builder."""
    return {
        "id": id, "name": name, "cuisine": cuisine, "primary_protein": protein,
        "ingredients": ingredients, "serves": serves, "active_minutes": minutes,
        "complexity": complexity,
        "dietary_flags": {
            "gluten_free": gf, "dairy_free": df, "nut_free": nut_free,
            "vegetarian": veg, "vegan": vegan, "low_carb": low_carb,
        },
        "tags": tags or [],
    }

def _i(name, qty, unit, category, pantry_stable=False):
    """Compact ingredient builder."""
    return {"name": name, "qty": qty, "unit": unit,
            "category": category, "pantry_stable": pantry_stable}

# ─────────────────────────────────────────────────────────────────────────────
# MEXICAN  (MEX-001 → MEX-030)
# ─────────────────────────────────────────────────────────────────────────────
MEXICAN = [
    _r("MEX-001", "Weeknight Chicken Tacos", "mexican", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("corn tortillas", 12, "count", "grain"),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["quick", "family-friendly"]),

    _r("MEX-002", "Smoky Beef Fajitas", "mexican", "beef", [
        _i("beef skirt steak", 1.5, "lbs", "protein"),
        _i("bell peppers", 3, "count", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("flour tortillas", 8, "count", "grain"),
        _i("lime", 2, "count", "produce"),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("garlic powder", 0.5, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["quick", "crowd-pleaser"]),

    _r("MEX-003", "Pork Carnitas Bowls", "mexican", "pork", [
        _i("pork shoulder", 2, "lbs", "protein"),
        _i("orange", 1, "count", "produce"),
        _i("lime", 2, "count", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("dried oregano", 1, "tsp", "spice", True),
        _i("cooked rice", 2, "cups", "grain"),
        _i("cilantro", 1, "bunch", "produce"),
    ], 4, 40, "weekend", gf=True, df=True, tags=["batch-friendly", "crowd-pleaser"]),

    _r("MEX-004", "Shrimp Tacos with Slaw", "mexican", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("corn tortillas", 12, "count", "grain"),
        _i("cabbage", 0.5, "head", "produce"),
        _i("lime", 3, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("sour cream", 0.5, "cup", "dairy"),
        _i("chipotle peppers in adobo", 2, "count", "canned", True),
        _i("garlic", 2, "cloves", "produce", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=True, tags=["quick", "light"]),

    _r("MEX-005", "Chicken Enchiladas Verde", "mexican", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("salsa verde", 16, "oz", "canned"),
        _i("corn tortillas", 12, "count", "grain"),
        _i("Monterey jack cheese", 2, "cups", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("sour cream", 0.5, "cup", "dairy"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
    ], 4, 45, "weekend", gf=True, tags=["comfort", "family-friendly"]),

    _r("MEX-006", "Beef and Bean Burritos", "mexican", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("large flour tortillas", 6, "count", "grain"),
        _i("black beans", 15, "oz", "canned", True),
        _i("cheddar cheese", 1.5, "cups", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("salsa", 1, "cup", "canned", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("garlic", 3, "cloves", "produce", True),
    ], 4, 25, "weeknight", tags=["quick", "family-friendly"]),

    _r("MEX-007", "Chicken Tortilla Soup", "mexican", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("chicken broth", 32, "oz", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("black beans", 15, "oz", "canned", True),
        _i("corn", 1, "cup", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("tortilla strips", 1, "cup", "grain"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
    ], 6, 35, "weeknight", gf=True, df=True, tags=["soup", "batch-friendly"]),

    _r("MEX-008", "Carne Asada Bowls", "mexican", "beef", [
        _i("beef flank steak", 1.5, "lbs", "protein"),
        _i("lime", 3, "count", "produce"),
        _i("orange", 1, "count", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("cilantro", 1, "bunch", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("cooked rice", 2, "cups", "grain"),
        _i("black beans", 15, "oz", "canned", True),
        _i("avocado", 2, "count", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=True, df=True, tags=["crowd-pleaser"]),

    _r("MEX-009", "Pork Chili Verde", "mexican", "pork", [
        _i("pork shoulder", 2, "lbs", "protein"),
        _i("salsa verde", 16, "oz", "canned"),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("poblano peppers", 2, "count", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("dried oregano", 1, "tsp", "spice", True),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
    ], 6, 50, "weekend", gf=True, df=True, tags=["batch-friendly", "comfort"]),

    _r("MEX-010", "Turkey Stuffed Peppers Tex-Mex", "mexican", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("bell peppers", 4, "count", "produce"),
        _i("cooked rice", 1, "cup", "grain"),
        _i("black beans", 15, "oz", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("Mexican blend cheese", 1, "cup", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
    ], 4, 50, "weekend", gf=True, tags=["family-friendly", "meal-prep"]),

    _r("MEX-011", "Chicken Tinga Tostadas", "mexican", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("chipotle peppers in adobo", 3, "count", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("tostada shells", 8, "count", "grain"),
        _i("refried beans", 15, "oz", "canned", True),
        _i("queso fresco", 4, "oz", "dairy"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("lime", 2, "count", "produce"),
    ], 4, 40, "weeknight", gf=True, tags=["crowd-pleaser"]),

    _r("MEX-012", "Beef Picadillo", "mexican", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("russet potatoes", 2, "medium", "produce"),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("green olives", 0.5, "cup", "canned", True),
        _i("raisins", 0.25, "cup", "pantry", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("cooked rice", 2, "cups", "grain"),
    ], 4, 35, "weeknight", gf=True, df=True, tags=["budget", "family-friendly"]),

    _r("MEX-013", "Shrimp and Corn Quesadillas", "mexican", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("large flour tortillas", 6, "count", "grain"),
        _i("Monterey jack cheese", 2, "cups", "dairy"),
        _i("corn", 1, "cup", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 0.5, "bunch", "produce"),
        _i("cumin", 0.5, "tsp", "spice", True),
        _i("butter", 2, "tbsp", "dairy", True),
    ], 4, 25, "weeknight", tags=["quick", "kid-friendly"]),

    _r("MEX-014", "Chicken Pozole Rojo", "mexican", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("hominy", 29, "oz", "canned"),
        _i("chicken broth", 32, "oz", "canned", True),
        _i("dried guajillo chiles", 4, "count", "spice"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("dried oregano", 1, "tsp", "spice", True),
        _i("cabbage", 0.5, "head", "produce"),
        _i("radishes", 1, "bunch", "produce"),
        _i("lime", 3, "count", "produce"),
    ], 6, 55, "weekend", gf=True, df=True, tags=["comfort", "batch-friendly"]),

    _r("MEX-015", "Arroz con Pollo", "mexican", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("long grain rice", 1.5, "cups", "grain"),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("bell pepper", 1, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("saffron", 0.25, "tsp", "spice", True),
        _i("frozen peas", 0.5, "cup", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 45, "weeknight", gf=True, df=True, tags=["one-pot", "family-friendly"]),

    _r("MEX-016", "Salmon Tacos with Mango Slaw", "mexican", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("corn tortillas", 12, "count", "grain"),
        _i("mango", 1, "count", "produce"),
        _i("cabbage", 0.5, "head", "produce"),
        _i("lime", 3, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("chipotle powder", 0.5, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["light", "fresh"]),

    _r("MEX-017", "Lamb Birria-Style Tacos", "mexican", "lamb", [
        _i("lamb shoulder", 2, "lbs", "protein"),
        _i("dried ancho chiles", 3, "count", "spice"),
        _i("dried guajillo chiles", 3, "count", "spice"),
        _i("beef broth", 2, "cups", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("corn tortillas", 12, "count", "grain"),
        _i("Oaxacan cheese", 1, "cup", "dairy"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("white onion", 0.5, "medium", "produce"),
        _i("lime", 2, "count", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("dried oregano", 1, "tsp", "spice", True),
    ], 4, 60, "weekend", gf=True, tags=["weekend-project", "crowd-pleaser"]),

    _r("MEX-018", "Turkey Black Bean Chili Blanco", "mexican", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("white beans", 30, "oz", "canned", True),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("diced green chiles", 7, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("sour cream", 0.5, "cup", "dairy"),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
    ], 6, 35, "weeknight", gf=True, tags=["batch-friendly", "comfort"]),

    _r("MEX-019", "Chicken Tamale Casserole", "mexican", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("cornmeal", 1.5, "cups", "grain"),
        _i("enchilada sauce", 19, "oz", "canned"),
        _i("diced green chiles", 7, "oz", "canned", True),
        _i("Mexican blend cheese", 1.5, "cups", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("butter", 3, "tbsp", "dairy", True),
    ], 6, 55, "weekend", gf=True, tags=["comfort", "family-friendly", "meal-prep"]),

    _r("MEX-020", "Beef Barbacoa Bowls", "mexican", "beef", [
        _i("beef chuck roast", 2, "lbs", "protein"),
        _i("chipotle peppers in adobo", 4, "count", "canned", True),
        _i("beef broth", 1, "cup", "canned", True),
        _i("lime", 2, "count", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("white onion", 1, "medium", "produce"),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("dried oregano", 1, "tsp", "spice", True),
        _i("cooked rice", 2, "cups", "grain"),
        _i("black beans", 15, "oz", "canned", True),
        _i("cilantro", 1, "bunch", "produce"),
    ], 4, 50, "weekend", gf=True, df=True, tags=["batch-friendly", "crowd-pleaser"]),

    _r("MEX-021", "Vegetable Enchiladas Rojo", "mexican", "eggs", [
        _i("eggs", 4, "count", "protein"),
        _i("zucchini", 2, "medium", "produce"),
        _i("black beans", 15, "oz", "canned", True),
        _i("corn tortillas", 12, "count", "grain"),
        _i("enchilada sauce", 19, "oz", "canned"),
        _i("Mexican blend cheese", 2, "cups", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("cilantro", 1, "bunch", "produce"),
    ], 4, 45, "weekend", gf=True, veg=True, tags=["vegetarian", "family-friendly"]),

    _r("MEX-022", "Pork Taco Salad", "mexican", "pork", [
        _i("ground pork", 1, "lb", "protein"),
        _i("romaine lettuce", 1, "head", "produce"),
        _i("black beans", 15, "oz", "canned", True),
        _i("corn", 1, "cup", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("avocado", 2, "count", "produce"),
        _i("tortilla strips", 1, "cup", "grain"),
        _i("Mexican blend cheese", 0.5, "cup", "dairy"),
        _i("lime", 2, "count", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 20, "weeknight", gf=True, tags=["quick", "light"]),

    _r("MEX-023", "Chicken Chilaquiles Rojos", "mexican", "chicken", [
        _i("chicken thighs", 1, "lb", "protein"),
        _i("tortilla chips", 4, "cups", "grain"),
        _i("enchilada sauce", 19, "oz", "canned"),
        _i("eggs", 4, "count", "protein"),
        _i("Mexican blend cheese", 1, "cup", "dairy"),
        _i("white onion", 0.5, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("sour cream", 0.5, "cup", "dairy"),
        _i("cilantro", 0.5, "bunch", "produce"),
        _i("avocado", 1, "count", "produce"),
    ], 4, 30, "weeknight", gf=True, tags=["brunch-style", "comfort"]),

    _r("MEX-024", "Chorizo Rice and Bean Bowls", "mexican", "pork", [
        _i("Mexican chorizo", 1, "lb", "protein"),
        _i("long grain rice", 1.5, "cups", "grain"),
        _i("pinto beans", 15, "oz", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("cilantro", 1, "bunch", "produce"),
        _i("lime", 2, "count", "produce"),
    ], 4, 35, "weeknight", gf=True, df=True, tags=["one-pot", "budget"]),

    _r("MEX-025", "Chicken and Sweet Potato Soup", "mexican", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("sweet potato", 2, "medium", "produce"),
        _i("chicken broth", 32, "oz", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
    ], 6, 40, "weeknight", gf=True, df=True, tags=["soup", "healthy", "batch-friendly"]),

    _r("MEX-026", "Beef Street Taco Bowls", "mexican", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("cooked rice", 2, "cups", "grain"),
        _i("pinto beans", 15, "oz", "canned", True),
        _i("corn", 1, "cup", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("avocado", 2, "count", "produce"),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 0.5, "bunch", "produce"),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("garlic powder", 0.5, "tsp", "spice", True),
        _i("olive oil", 1, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["quick", "meal-prep"]),

    _r("MEX-027", "Pork Posole Verde", "mexican", "pork", [
        _i("pork tenderloin", 1.5, "lbs", "protein"),
        _i("hominy", 29, "oz", "canned"),
        _i("salsa verde", 16, "oz", "canned"),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("dried oregano", 1, "tsp", "spice", True),
        _i("lime", 2, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("radishes", 1, "bunch", "produce"),
        _i("cabbage", 0.25, "head", "produce"),
    ], 6, 45, "weekend", gf=True, df=True, tags=["batch-friendly", "comfort"]),

    _r("MEX-028", "Shrimp and Avocado Tostadas", "mexican", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("tostada shells", 8, "count", "grain"),
        _i("avocado", 2, "count", "produce"),
        _i("lime", 3, "count", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("cilantro", 1, "bunch", "produce"),
        _i("refried beans", 15, "oz", "canned", True),
        _i("cumin", 0.5, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 20, "weeknight", gf=True, tags=["quick", "fresh", "light"]),

    _r("MEX-029", "Chicken Mole-Style Bowls", "mexican", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("mole sauce", 8, "oz", "canned"),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("cooked rice", 2, "cups", "grain"),
        _i("black beans", 15, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("cilantro", 1, "bunch", "produce"),
    ], 4, 40, "weekend", gf=True, df=True, tags=["bold-flavors", "comfort"]),

    _r("MEX-030", "Turkey and Pepper Fajita Bowls", "mexican", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("bell peppers", 3, "count", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("cooked rice", 2, "cups", "grain"),
        _i("black beans", 15, "oz", "canned", True),
        _i("lime", 2, "count", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("smoked paprika", 0.5, "tsp", "spice", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["quick", "healthy"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# ITALIAN  (ITA-001 → ITA-030)
# ─────────────────────────────────────────────────────────────────────────────
ITALIAN = [
    _r("ITA-001", "Weeknight Bolognese", "italian", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("spaghetti", 12, "oz", "grain"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("dry red wine", 0.5, "cup", "pantry", True),
        _i("whole milk", 0.5, "cup", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("dried oregano", 1, "tsp", "spice", True),
    ], 4, 45, "weeknight", tags=["classic", "comfort", "family-friendly"]),

    _r("ITA-002", "Chicken Piccata", "italian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("butter", 4, "tbsp", "dairy", True),
        _i("lemon", 2, "count", "produce"),
        _i("capers", 2, "tbsp", "canned", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("all-purpose flour", 0.5, "cup", "pantry", True),
        _i("white wine", 0.5, "cup", "pantry", True),
        _i("angel hair pasta", 12, "oz", "grain"),
        _i("fresh parsley", 0.25, "cup", "produce"),
    ], 4, 30, "weeknight", nut_free=True, tags=["classic", "elegant", "quick"]),

    _r("ITA-003", "One-Pan Chicken Marsala", "italian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("cremini mushrooms", 8, "oz", "produce"),
        _i("Marsala wine", 0.75, "cup", "pantry"),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("heavy cream", 0.5, "cup", "dairy"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("all-purpose flour", 0.5, "cup", "pantry", True),
        _i("egg noodles", 12, "oz", "grain"),
        _i("fresh thyme", 4, "sprigs", "produce"),
    ], 4, 35, "weeknight", nut_free=True, tags=["classic", "comfort"]),

    _r("ITA-004", "Sausage and Peppers Sheet Pan", "italian", "pork", [
        _i("Italian sausage links", 1.5, "lbs", "protein"),
        _i("bell peppers", 3, "count", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("Italian seasoning", 1, "tsp", "spice", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
        _i("hoagie rolls", 4, "count", "grain"),
    ], 4, 40, "weeknight", df=True, nut_free=True, tags=["sheet-pan", "crowd-pleaser"]),

    _r("ITA-005", "Shrimp Scampi", "italian", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("linguine", 12, "oz", "grain"),
        _i("butter", 4, "tbsp", "dairy", True),
        _i("garlic", 6, "cloves", "produce", True),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("lemon", 2, "count", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", nut_free=True, tags=["quick", "elegant", "classic"]),

    _r("ITA-006", "Beef Meatballs in Sunday Sauce", "italian", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("ground pork", 0.5, "lb", "protein"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("breadcrumbs", 0.5, "cup", "grain", True),
        _i("egg", 1, "count", "dairy", True),
        _i("Parmesan cheese", 0.75, "cup", "dairy"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("spaghetti", 12, "oz", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 6, 50, "weekend", nut_free=True, tags=["classic", "comfort", "batch-friendly"]),

    _r("ITA-007", "Chicken Parmesan", "italian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("marinara sauce", 24, "oz", "canned"),
        _i("mozzarella cheese", 8, "oz", "dairy"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("breadcrumbs", 1, "cup", "grain", True),
        _i("egg", 2, "count", "dairy", True),
        _i("penne pasta", 12, "oz", "grain"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("Italian seasoning", 1, "tsp", "spice", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 45, "weeknight", nut_free=True, tags=["classic", "family-favorite", "comfort"]),

    _r("ITA-008", "Pork Ragu with Pappardelle", "italian", "pork", [
        _i("pork shoulder", 2, "lbs", "protein"),
        _i("pappardelle pasta", 12, "oz", "grain"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("dry red wine", 1, "cup", "pantry", True),
        _i("white onion", 1, "medium", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh rosemary", 2, "sprigs", "produce"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 6, 120, "weekend", nut_free=True, tags=["slow-cook", "comfort", "special-occasion"]),

    _r("ITA-009", "Salmon with Lemon Caper Butter", "italian", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("butter", 4, "tbsp", "dairy", True),
        _i("capers", 2, "tbsp", "canned", True),
        _i("lemon", 2, "count", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh dill", 1, "bunch", "produce"),
        _i("asparagus", 1, "lb", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("white wine", 0.25, "cup", "pantry", True),
    ], 4, 25, "weeknight", gf=True, nut_free=True, tags=["quick", "elegant", "light"]),

    _r("ITA-010", "Turkey and Spinach Stuffed Shells", "italian", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("jumbo pasta shells", 20, "count", "grain"),
        _i("ricotta cheese", 15, "oz", "dairy"),
        _i("frozen spinach", 10, "oz", "produce"),
        _i("marinara sauce", 24, "oz", "canned"),
        _i("mozzarella cheese", 8, "oz", "dairy"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("egg", 1, "count", "dairy", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("Italian seasoning", 1, "tsp", "spice", True),
    ], 6, 55, "weekend", nut_free=True, tags=["comfort", "batch-friendly", "family-favorite"]),

    _r("ITA-011", "Baked Ziti with Italian Sausage", "italian", "pork", [
        _i("Italian sausage", 1, "lb", "protein"),
        _i("ziti pasta", 12, "oz", "grain"),
        _i("marinara sauce", 24, "oz", "canned"),
        _i("ricotta cheese", 15, "oz", "dairy"),
        _i("mozzarella cheese", 2, "cups", "dairy"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("white onion", 1, "medium", "produce"),
        _i("Italian seasoning", 1, "tsp", "spice", True),
    ], 6, 50, "weekend", nut_free=True, tags=["comfort", "batch-friendly", "family-favorite"]),

    _r("ITA-012", "Chicken Cacciatore", "italian", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("cremini mushrooms", 8, "oz", "produce"),
        _i("bell peppers", 2, "count", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("dry red wine", 0.5, "cup", "pantry", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("black olives", 0.5, "cup", "canned", True),
        _i("fresh thyme", 4, "sprigs", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 50, "weekend", gf=True, df=True, nut_free=True, tags=["classic", "comfort", "one-pot"]),

    _r("ITA-013", "Italian Wedding Soup", "italian", "beef", [
        _i("ground beef", 0.75, "lb", "protein"),
        _i("ground pork", 0.25, "lb", "protein"),
        _i("chicken broth", 48, "oz", "canned", True),
        _i("acini di pepe pasta", 1, "cup", "grain"),
        _i("fresh spinach", 4, "cups", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("egg", 1, "count", "dairy", True),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("breadcrumbs", 0.5, "cup", "grain", True),
        _i("garlic", 3, "cloves", "produce", True),
    ], 6, 40, "weeknight", nut_free=True, tags=["soup", "comfort", "batch-friendly"]),

    _r("ITA-014", "Arrabbiata with Italian Sausage", "italian", "pork", [
        _i("Italian sausage", 1, "lb", "protein"),
        _i("penne pasta", 12, "oz", "grain"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("garlic", 6, "cloves", "produce", True),
        _i("red pepper flakes", 1, "tsp", "spice", True),
        _i("fresh basil", 0.5, "cup", "produce"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("olive oil", 3, "tbsp", "pantry", True),
        _i("white wine", 0.25, "cup", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["quick", "bold-flavors", "spicy"]),

    _r("ITA-015", "Tuscan White Bean Chicken Skillet", "italian", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("cannellini beans", 30, "oz", "canned", True),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("fresh spinach", 4, "cups", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("heavy cream", 0.5, "cup", "dairy"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("fresh thyme", 4, "sprigs", "produce"),
        _i("sun-dried tomatoes", 0.25, "cup", "canned", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["one-pan", "comfort", "low-carb"]),

    _r("ITA-016", "Eggplant Parmesan", "italian", "eggs", [
        _i("eggs", 3, "count", "protein"),
        _i("eggplant", 2, "large", "produce"),
        _i("marinara sauce", 24, "oz", "canned"),
        _i("mozzarella cheese", 2, "cups", "dairy"),
        _i("Parmesan cheese", 1, "cup", "dairy"),
        _i("breadcrumbs", 1.5, "cups", "grain", True),
        _i("Italian seasoning", 1, "tsp", "spice", True),
        _i("garlic powder", 0.5, "tsp", "spice", True),
        _i("olive oil", 4, "tbsp", "pantry", True),
        _i("spaghetti", 12, "oz", "grain"),
    ], 4, 55, "weekend", veg=True, nut_free=True, tags=["vegetarian", "classic", "comfort"]),

    _r("ITA-017", "Shrimp Fra Diavolo", "italian", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("linguine", 12, "oz", "grain"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("garlic", 6, "cloves", "produce", True),
        _i("red pepper flakes", 1.5, "tsp", "spice", True),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("lemon", 1, "count", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", df=True, nut_free=True, tags=["quick", "spicy", "elegant"]),

    _r("ITA-018", "Pork Tenderloin with Rosemary Pan Sauce", "italian", "pork", [
        _i("pork tenderloin", 1.5, "lbs", "protein"),
        _i("fresh rosemary", 3, "sprigs", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("lemon", 1, "count", "produce"),
        _i("roasted potatoes", 1.5, "lbs", "produce"),
        _i("asparagus", 1, "lb", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
        _i("Dijon mustard", 1, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["elegant", "low-carb"]),

    _r("ITA-019", "Lamb Ragu with Rigatoni", "italian", "lamb", [
        _i("ground lamb", 1.5, "lbs", "protein"),
        _i("rigatoni pasta", 12, "oz", "grain"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("dry red wine", 0.75, "cup", "pantry", True),
        _i("white onion", 1, "medium", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh rosemary", 2, "sprigs", "produce"),
        _i("Pecorino Romano", 0.5, "cup", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 50, "weekend", nut_free=True, tags=["bold-flavors", "special-occasion"]),

    _r("ITA-020", "Cioppino", "italian", "shrimp", [
        _i("shrimp", 0.75, "lb", "protein"),
        _i("fish fillets", 0.75, "lb", "protein"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("clam juice", 8, "oz", "canned"),
        _i("dry white wine", 1, "cup", "pantry", True),
        _i("fennel bulb", 1, "medium", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("sourdough bread", 1, "loaf", "grain"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 45, "weekend", gf=False, df=True, nut_free=True, tags=["seafood", "special-occasion"]),

    _r("ITA-021", "One-Pot Chicken Florentine Pasta", "italian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("penne pasta", 12, "oz", "grain"),
        _i("fresh spinach", 4, "cups", "produce"),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("heavy cream", 0.75, "cup", "dairy"),
        _i("Parmesan cheese", 0.75, "cup", "dairy"),
        _i("sun-dried tomatoes", 0.25, "cup", "canned", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("Italian seasoning", 1, "tsp", "spice", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["one-pot", "creamy", "family-favorite"]),

    _r("ITA-022", "Beef Braised Short Ribs", "italian", "beef", [
        _i("beef short ribs", 3, "lbs", "protein"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("dry red wine", 1.5, "cups", "pantry", True),
        _i("beef broth", 2, "cups", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("carrots", 3, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("fresh thyme", 4, "sprigs", "produce"),
        _i("fresh rosemary", 2, "sprigs", "produce"),
        _i("egg noodles", 12, "oz", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 150, "weekend", gf=False, df=True, nut_free=True, tags=["slow-cook", "special-occasion", "comfort"]),

    _r("ITA-023", "Tomato Braised Chicken Thighs", "italian", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("capers", 2, "tbsp", "canned", True),
        _i("fresh basil", 0.5, "cup", "produce"),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("crusty bread", 1, "loaf", "grain"),
    ], 4, 45, "weeknight", gf=False, df=True, nut_free=True, tags=["one-pot", "bold-flavors"]),

    _r("ITA-024", "Pork Saltimbocca", "italian", "pork", [
        _i("pork cutlets", 1.5, "lbs", "protein"),
        _i("prosciutto", 4, "oz", "protein"),
        _i("fresh sage", 16, "leaves", "produce"),
        _i("butter", 4, "tbsp", "dairy", True),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("chicken broth", 0.25, "cup", "canned", True),
        _i("lemon", 1, "count", "produce"),
        _i("roasted potatoes", 1.5, "lbs", "produce"),
        _i("all-purpose flour", 0.25, "cup", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["elegant", "quick", "classic"]),

    _r("ITA-025", "Vegetable Minestrone", "italian", "eggs", [
        _i("eggs", 2, "count", "protein"),
        _i("cannellini beans", 15, "oz", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("vegetable broth", 48, "oz", "canned", True),
        _i("zucchini", 2, "medium", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("small pasta", 1, "cup", "grain"),
        _i("Parmesan rind", 1, "piece", "dairy", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 6, 40, "weeknight", veg=True, nut_free=True, tags=["soup", "vegetarian", "batch-friendly"]),

    _r("ITA-026", "Ground Beef Bolognese Lasagna", "italian", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("lasagna noodles", 12, "count", "grain"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("ricotta cheese", 15, "oz", "dairy"),
        _i("mozzarella cheese", 3, "cups", "dairy"),
        _i("Parmesan cheese", 1, "cup", "dairy"),
        _i("egg", 1, "count", "dairy", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("Italian seasoning", 2, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 8, 80, "weekend", nut_free=True, tags=["meal-prep", "comfort", "family-favorite"]),

    _r("ITA-027", "Salmon Puttanesca", "italian", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("capers", 2, "tbsp", "canned", True),
        _i("anchovy paste", 1, "tsp", "canned", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("linguine", 12, "oz", "grain"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", df=True, nut_free=True, tags=["bold-flavors", "quick", "elegant"]),

    _r("ITA-028", "Chicken and Artichoke Baked Pasta", "italian", "chicken", [
        _i("chicken breast", 1, "lb", "protein"),
        _i("rigatoni pasta", 12, "oz", "grain"),
        _i("artichoke hearts", 14, "oz", "canned", True),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("heavy cream", 0.75, "cup", "dairy"),
        _i("mozzarella cheese", 1.5, "cups", "dairy"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("Italian seasoning", 1, "tsp", "spice", True),
    ], 6, 50, "weekend", nut_free=True, tags=["baked", "comfort", "family-friendly"]),

    _r("ITA-029", "Turkey Polpette in Marinara", "italian", "turkey", [
        _i("ground turkey", 1.5, "lbs", "protein"),
        _i("marinara sauce", 24, "oz", "canned"),
        _i("breadcrumbs", 0.5, "cup", "grain", True),
        _i("egg", 1, "count", "dairy", True),
        _i("Parmesan cheese", 0.75, "cup", "dairy"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("spaghetti", 12, "oz", "grain"),
        _i("Italian seasoning", 1, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 40, "weeknight", nut_free=True, tags=["family-favorite", "lighter-version"]),

    _r("ITA-030", "Shrimp and Fennel Risotto", "italian", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("arborio rice", 1.5, "cups", "grain"),
        _i("fennel bulb", 1, "medium", "produce"),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("chicken broth", 4, "cups", "canned", True),
        _i("shallots", 2, "count", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("lemon", 1, "count", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
    ], 4, 40, "weekend", gf=True, nut_free=True, tags=["elegant", "special-occasion"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# ASIAN  (ASN-001 → ASN-030)
# ─────────────────────────────────────────────────────────────────────────────
ASIAN = [
    _r("ASN-001", "Weeknight Chicken Stir-Fry", "asian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("broccoli", 1, "head", "produce"),
        _i("bell peppers", 2, "count", "produce"),
        _i("snap peas", 1, "cup", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tbsp", "pantry", True),
        _i("cornstarch", 1, "tbsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
    ], 4, 25, "weeknight", df=True, nut_free=True, tags=["quick", "healthy", "classic"]),

    _r("ASN-002", "Beef and Broccoli", "asian", "beef", [
        _i("beef flank steak", 1.5, "lbs", "protein"),
        _i("broccoli", 1, "large head", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("oyster sauce", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("cornstarch", 1, "tbsp", "pantry", True),
        _i("brown sugar", 1, "tbsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
    ], 4, 30, "weeknight", df=True, nut_free=True, tags=["classic", "takeout-style", "crowd-pleaser"]),

    _r("ASN-003", "Pork Fried Rice", "asian", "pork", [
        _i("ground pork", 1, "lb", "protein"),
        _i("cooked white rice", 3, "cups", "grain"),
        _i("eggs", 3, "count", "dairy"),
        _i("frozen peas and carrots", 1, "cup", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 20, "weeknight", df=True, nut_free=True, tags=["quick", "budget", "crowd-pleaser"]),

    _r("ASN-004", "Shrimp Pad Thai", "asian", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("rice noodles", 8, "oz", "grain"),
        _i("eggs", 2, "count", "dairy"),
        _i("bean sprouts", 2, "cups", "produce"),
        _i("green onions", 4, "stalks", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fish sauce", 2, "tbsp", "pantry", True),
        _i("lime", 2, "count", "produce"),
        _i("peanuts", 0.5, "cup", "pantry"),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("tamarind paste", 2, "tbsp", "pantry", True),
        _i("brown sugar", 1, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=True, df=True, tags=["classic", "takeout-style"]),

    _r("ASN-005", "Chicken Teriyaki Bowls", "asian", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("mirin", 2, "tbsp", "pantry", True),
        _i("brown sugar", 2, "tbsp", "pantry", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh ginger", 1, "tsp", "produce", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("broccoli", 1, "head", "produce"),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 30, "weeknight", df=True, nut_free=True, tags=["family-favorite", "crowd-pleaser"]),

    _r("ASN-006", "Korean Beef Bulgogi Bowls", "asian", "beef", [
        _i("beef ribeye or sirloin", 1.5, "lbs", "protein"),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("sesame oil", 2, "tbsp", "pantry", True),
        _i("brown sugar", 2, "tbsp", "pantry", True),
        _i("garlic", 6, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("Asian pear", 0.5, "count", "produce"),
        _i("green onions", 4, "stalks", "produce"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("kimchi", 1, "cup", "produce"),
    ], 4, 35, "weeknight", df=True, nut_free=True, tags=["bold-flavors", "crowd-pleaser"]),

    _r("ASN-007", "Chicken Tikka Masala", "asian", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("coconut milk", 13.5, "oz", "canned"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh ginger", 2, "tbsp", "produce", True),
        _i("garam masala", 2, "tsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("plain yogurt", 0.5, "cup", "dairy"),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("cooked basmati rice", 2, "cups", "grain"),
        _i("fresh cilantro", 0.5, "bunch", "produce"),
    ], 4, 40, "weeknight", gf=True, nut_free=True, tags=["crowd-pleaser", "bold-flavors", "comfort"]),

    _r("ASN-008", "Pork Tonkatsu with Rice", "asian", "pork", [
        _i("pork loin chops", 1.5, "lbs", "protein"),
        _i("panko breadcrumbs", 1.5, "cups", "grain"),
        _i("eggs", 2, "count", "dairy"),
        _i("all-purpose flour", 0.5, "cup", "pantry", True),
        _i("cabbage", 0.5, "head", "produce"),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("tonkatsu sauce", 0.5, "cup", "pantry"),
        _i("vegetable oil", 1, "cup", "pantry", True),
        _i("lemon", 1, "count", "produce"),
    ], 4, 35, "weeknight", df=True, nut_free=True, tags=["crispy", "crowd-pleaser", "family-friendly"]),

    _r("ASN-009", "Miso-Glazed Salmon", "asian", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("white miso paste", 3, "tbsp", "pantry"),
        _i("mirin", 2, "tbsp", "pantry", True),
        _i("soy sauce", 1, "tbsp", "pantry", True),
        _i("brown sugar", 1, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("bok choy", 2, "heads", "produce"),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 25, "weeknight", df=True, nut_free=True, tags=["elegant", "healthy", "quick"]),

    _r("ASN-010", "General Tso's Chicken", "asian", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("hoisin sauce", 2, "tbsp", "pantry", True),
        _i("rice vinegar", 2, "tbsp", "pantry", True),
        _i("brown sugar", 3, "tbsp", "pantry", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("dried red chiles", 4, "count", "spice", True),
        _i("cornstarch", 2, "tbsp", "pantry", True),
        _i("egg", 1, "count", "dairy", True),
        _i("vegetable oil", 1, "cup", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 40, "weeknight", df=True, nut_free=True, tags=["takeout-style", "crowd-pleaser"]),

    _r("ASN-011", "Shrimp Thai Basil", "asian", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("fresh Thai basil", 1, "cup", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("bird's eye chiles", 3, "count", "produce"),
        _i("fish sauce", 2, "tbsp", "pantry", True),
        _i("oyster sauce", 1, "tbsp", "pantry", True),
        _i("soy sauce", 1, "tbsp", "pantry", True),
        _i("brown sugar", 1, "tsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("cooked jasmine rice", 2, "cups", "grain"),
        _i("eggs", 4, "count", "dairy"),
    ], 4, 20, "weeknight", gf=True, df=True, nut_free=True, tags=["quick", "spicy", "bold-flavors"]),

    _r("ASN-012", "Kung Pao Chicken", "asian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("peanuts", 0.5, "cup", "pantry"),
        _i("dried red chiles", 6, "count", "spice", True),
        _i("bell peppers", 2, "count", "produce"),
        _i("green onions", 4, "stalks", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("rice vinegar", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("cornstarch", 1, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
    ], 4, 30, "weeknight", df=True, tags=["spicy", "takeout-style", "classic"]),

    _r("ASN-013", "Pork Ramen Bowls", "asian", "pork", [
        _i("pork belly or shoulder", 1.5, "lbs", "protein"),
        _i("ramen noodles", 12, "oz", "grain"),
        _i("chicken broth", 48, "oz", "canned", True),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("miso paste", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tbsp", "pantry", True),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh ginger", 2, "tbsp", "produce", True),
        _i("bok choy", 2, "heads", "produce"),
        _i("eggs", 4, "count", "dairy"),
        _i("green onions", 4, "stalks", "produce"),
        _i("nori sheets", 4, "count", "pantry", True),
    ], 4, 60, "weekend", df=True, nut_free=True, tags=["comfort", "weekend-project"]),

    _r("ASN-014", "Beef Bibimbap Bowls", "asian", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("cooked short-grain rice", 2, "cups", "grain"),
        _i("spinach", 2, "cups", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("zucchini", 1, "medium", "produce"),
        _i("shiitake mushrooms", 4, "oz", "produce"),
        _i("eggs", 4, "count", "dairy"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("sesame oil", 2, "tbsp", "pantry", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("gochujang", 2, "tbsp", "pantry"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
    ], 4, 45, "weekend", gf=True, df=True, nut_free=True, tags=["colorful", "healthy", "weekend"]),

    _r("ASN-015", "Turkey Asian Lettuce Wraps", "asian", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("butter lettuce", 2, "heads", "produce"),
        _i("water chestnuts", 8, "oz", "canned", True),
        _i("cremini mushrooms", 4, "oz", "produce"),
        _i("green onions", 4, "stalks", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("hoisin sauce", 3, "tbsp", "pantry", True),
        _i("soy sauce", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("rice vinegar", 1, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=True, df=True, nut_free=True, tags=["light", "quick", "low-carb"]),

    _r("ASN-016", "Pork Char Siu Rice Bowls", "asian", "pork", [
        _i("pork tenderloin", 1.5, "lbs", "protein"),
        _i("hoisin sauce", 3, "tbsp", "pantry", True),
        _i("soy sauce", 2, "tbsp", "pantry", True),
        _i("honey", 2, "tbsp", "pantry", True),
        _i("five-spice powder", 0.5, "tsp", "spice", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("bok choy", 2, "heads", "produce"),
        _i("green onions", 3, "stalks", "produce"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", df=True, nut_free=True, tags=["bold-flavors", "crowd-pleaser"]),

    _r("ASN-017", "Salmon Teriyaki Bowls", "asian", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("mirin", 2, "tbsp", "pantry", True),
        _i("brown sugar", 2, "tbsp", "pantry", True),
        _i("garlic", 2, "cloves", "produce", True),
        _i("fresh ginger", 1, "tsp", "produce", True),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("edamame", 1, "cup", "produce"),
        _i("cucumber", 1, "medium", "produce"),
        _i("avocado", 1, "count", "produce"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 25, "weeknight", gf=True, df=True, nut_free=True, tags=["healthy", "quick", "elegant"]),

    _r("ASN-018", "Chicken Japanese Curry", "asian", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("Japanese curry roux", 1, "box", "pantry"),
        _i("potatoes", 2, "medium", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("chicken broth", 3, "cups", "canned", True),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
    ], 4, 45, "weeknight", df=True, nut_free=True, tags=["comfort", "family-friendly", "kid-friendly"]),

    _r("ASN-019", "Shrimp Singapore Noodles", "asian", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("rice vermicelli", 8, "oz", "grain"),
        _i("eggs", 2, "count", "dairy"),
        _i("bean sprouts", 2, "cups", "produce"),
        _i("bell peppers", 2, "count", "produce"),
        _i("green onions", 4, "stalks", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("curry powder", 2, "tsp", "spice", True),
        _i("soy sauce", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=True, df=True, nut_free=True, tags=["takeout-style", "bold-flavors"]),

    _r("ASN-020", "Chicken and Snow Pea Stir-Fry", "asian", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("snow peas", 2, "cups", "produce"),
        _i("water chestnuts", 8, "oz", "canned", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("oyster sauce", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("cornstarch", 1, "tbsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
    ], 4, 20, "weeknight", df=True, nut_free=True, tags=["quick", "healthy", "light"]),

    _r("ASN-021", "Dan Dan Noodles with Ground Pork", "asian", "pork", [
        _i("ground pork", 1, "lb", "protein"),
        _i("Chinese wheat noodles", 12, "oz", "grain"),
        _i("tahini", 3, "tbsp", "pantry", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("chili oil", 2, "tbsp", "pantry", True),
        _i("rice vinegar", 2, "tbsp", "pantry", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("green onions", 4, "stalks", "produce"),
        _i("bok choy", 2, "heads", "produce"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
    ], 4, 30, "weeknight", df=True, tags=["bold-flavors", "spicy", "noodles"]),

    _r("ASN-022", "Lamb Mongolian Stir-Fry", "asian", "lamb", [
        _i("lamb leg steak", 1.5, "lbs", "protein"),
        _i("green onions", 6, "stalks", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh ginger", 1.5, "tbsp", "produce", True),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("hoisin sauce", 2, "tbsp", "pantry", True),
        _i("brown sugar", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tbsp", "pantry", True),
        _i("dried red chiles", 3, "count", "spice", True),
        _i("cornstarch", 1, "tbsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
    ], 4, 30, "weeknight", df=True, nut_free=True, tags=["bold-flavors", "quick"]),

    _r("ASN-023", "Vegetable Fried Rice", "asian", "eggs", [
        _i("eggs", 4, "count", "protein"),
        _i("cooked white rice", 3, "cups", "grain"),
        _i("frozen peas", 1, "cup", "produce"),
        _i("carrots", 2, "medium", "produce"),
        _i("corn", 1, "cup", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 20, "weeknight", df=True, nut_free=True, veg=True, tags=["quick", "budget", "vegetarian"]),

    _r("ASN-024", "Beef Pepper Steak", "asian", "beef", [
        _i("beef sirloin", 1.5, "lbs", "protein"),
        _i("bell peppers", 3, "count", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("soy sauce", 4, "tbsp", "pantry", True),
        _i("oyster sauce", 2, "tbsp", "pantry", True),
        _i("cornstarch", 1, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("black pepper", 1, "tsp", "spice", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("cooked white rice", 2, "cups", "grain"),
    ], 4, 25, "weeknight", df=True, nut_free=True, tags=["classic", "takeout-style"]),

    _r("ASN-025", "Pork Gyoza Soup", "asian", "pork", [
        _i("frozen pork gyoza", 24, "count", "protein"),
        _i("chicken broth", 48, "oz", "canned", True),
        _i("bok choy", 2, "heads", "produce"),
        _i("shiitake mushrooms", 4, "oz", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("soy sauce", 2, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
        _i("chili oil", 1, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", df=True, nut_free=True, tags=["quick", "comfort", "soup"]),

    _r("ASN-026", "Chicken Sesame Noodles", "asian", "chicken", [
        _i("chicken breast", 1, "lb", "protein"),
        _i("spaghetti or lo mein noodles", 12, "oz", "grain"),
        _i("peanut butter", 3, "tbsp", "pantry", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("sesame oil", 2, "tbsp", "pantry", True),
        _i("rice vinegar", 2, "tbsp", "pantry", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh ginger", 1, "tsp", "produce", True),
        _i("cucumber", 1, "medium", "produce"),
        _i("green onions", 3, "stalks", "produce"),
        _i("sesame seeds", 1, "tbsp", "pantry", True),
        _i("chili oil", 1, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", df=True, tags=["noodles", "cold-or-hot", "crowd-pleaser"]),

    _r("ASN-027", "Shrimp Fried Rice", "asian", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("cooked white rice", 3, "cups", "grain"),
        _i("eggs", 2, "count", "dairy"),
        _i("frozen peas and carrots", 1, "cup", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("soy sauce", 3, "tbsp", "pantry", True),
        _i("sesame oil", 1, "tsp", "pantry", True),
        _i("oyster sauce", 1, "tbsp", "pantry", True),
        _i("vegetable oil", 2, "tbsp", "pantry", True),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 20, "weeknight", df=True, nut_free=True, tags=["quick", "crowd-pleaser"]),

    _r("ASN-028", "Beef Pho-Style Bowls", "asian", "beef", [
        _i("beef sirloin", 1, "lb", "protein"),
        _i("beef broth", 48, "oz", "canned", True),
        _i("rice noodles", 8, "oz", "grain"),
        _i("fresh ginger", 2, "tbsp", "produce", True),
        _i("star anise", 3, "count", "spice", True),
        _i("cinnamon stick", 1, "count", "spice", True),
        _i("fish sauce", 3, "tbsp", "pantry", True),
        _i("bean sprouts", 2, "cups", "produce"),
        _i("fresh basil", 1, "cup", "produce"),
        _i("lime", 2, "count", "produce"),
        _i("jalapeño", 1, "count", "produce"),
        _i("green onions", 3, "stalks", "produce"),
    ], 4, 40, "weekend", gf=True, df=True, nut_free=True, tags=["comfort", "soup", "weekend"]),

    _r("ASN-029", "Turkey Larb Bowls", "asian", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("cooked white rice", 2, "cups", "grain"),
        _i("shallots", 3, "count", "produce"),
        _i("lime", 3, "count", "produce"),
        _i("fresh mint", 0.5, "cup", "produce"),
        _i("fresh cilantro", 0.5, "cup", "produce"),
        _i("fish sauce", 2, "tbsp", "pantry", True),
        _i("toasted rice powder", 2, "tbsp", "pantry", True),
        _i("dried red chiles", 2, "tsp", "spice", True),
        _i("butter lettuce", 1, "head", "produce"),
        _i("cucumber", 1, "medium", "produce"),
    ], 4, 25, "weeknight", gf=True, df=True, nut_free=True, tags=["light", "fresh", "spicy"]),

    _r("ASN-030", "Lamb Saag-Style Bowls", "asian", "lamb", [
        _i("ground lamb", 1.5, "lbs", "protein"),
        _i("fresh spinach", 6, "cups", "produce"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh ginger", 2, "tbsp", "produce", True),
        _i("garam masala", 2, "tsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("turmeric", 0.5, "tsp", "spice", True),
        _i("plain yogurt", 0.5, "cup", "dairy"),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("cooked basmati rice", 2, "cups", "grain"),
    ], 4, 40, "weeknight", gf=True, nut_free=True, tags=["bold-flavors", "comfort"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# AMERICAN  (AMR-001 → AMR-030)
# ─────────────────────────────────────────────────────────────────────────────
AMERICAN = [
    _r("AMR-001", "Classic Beef Chili", "american", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("kidney beans", 30, "oz", "canned", True),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("bell pepper", 1, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("chili powder", 2, "tbsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("beef broth", 1, "cup", "canned", True),
        _i("cheddar cheese", 1, "cup", "dairy"),
        _i("sour cream", 0.5, "cup", "dairy"),
    ], 6, 45, "weeknight", gf=True, nut_free=True, tags=["comfort", "batch-friendly", "crowd-pleaser"]),

    _r("AMR-002", "Sheet Pan Chicken Thighs with Roasted Veg", "american", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("potatoes", 1.5, "lbs", "produce"),
        _i("broccoli", 1, "head", "produce"),
        _i("carrots", 3, "medium", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("dried thyme", 1, "tsp", "spice", True),
        _i("garlic powder", 0.5, "tsp", "spice", True),
        _i("lemon", 1, "count", "produce"),
    ], 4, 45, "weeknight", gf=True, df=True, nut_free=True, tags=["sheet-pan", "easy-cleanup", "family-friendly"]),

    _r("AMR-003", "Slow Cooker Pulled Pork", "american", "pork", [
        _i("pork shoulder", 3, "lbs", "protein"),
        _i("BBQ sauce", 1, "cup", "pantry"),
        _i("apple cider vinegar", 0.25, "cup", "pantry", True),
        _i("brown sugar", 2, "tbsp", "pantry", True),
        _i("smoked paprika", 1, "tbsp", "spice", True),
        _i("garlic powder", 1, "tsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("brioche buns", 6, "count", "grain"),
        _i("coleslaw mix", 1, "bag", "produce"),
    ], 6, 30, "weekend", df=True, nut_free=True, tags=["batch-friendly", "crowd-pleaser", "slow-cook"]),

    _r("AMR-004", "Pan-Seared Salmon with Green Beans", "american", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("green beans", 1, "lb", "produce"),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("lemon", 1, "count", "produce"),
        _i("fresh dill", 2, "tbsp", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("potatoes", 1, "lb", "produce"),
    ], 4, 30, "weeknight", gf=True, nut_free=True, tags=["healthy", "quick", "elegant"]),

    _r("AMR-005", "Turkey Meatloaf", "american", "turkey", [
        _i("ground turkey", 1.5, "lbs", "protein"),
        _i("breadcrumbs", 0.5, "cup", "grain", True),
        _i("egg", 1, "count", "dairy", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("ketchup", 0.5, "cup", "pantry", True),
        _i("Worcestershire sauce", 1, "tbsp", "pantry", True),
        _i("Dijon mustard", 1, "tbsp", "pantry", True),
        _i("mashed potatoes", 4, "servings", "produce"),
        _i("green beans", 1, "lb", "produce"),
    ], 4, 60, "weekend", nut_free=True, tags=["comfort", "family-favorite", "classic"]),

    _r("AMR-006", "Beef Pot Roast", "american", "beef", [
        _i("beef chuck roast", 3, "lbs", "protein"),
        _i("potatoes", 1.5, "lbs", "produce"),
        _i("carrots", 4, "medium", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 6, "cloves", "produce", True),
        _i("beef broth", 2, "cups", "canned", True),
        _i("tomato paste", 2, "tbsp", "canned", True),
        _i("Worcestershire sauce", 1, "tbsp", "pantry", True),
        _i("fresh thyme", 4, "sprigs", "produce"),
        _i("fresh rosemary", 2, "sprigs", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 6, 210, "weekend", gf=True, df=True, nut_free=True, tags=["slow-cook", "comfort", "special-occasion"]),

    _r("AMR-007", "Chicken Pot Pie Casserole", "american", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("frozen peas and carrots", 1.5, "cups", "produce"),
        _i("potatoes", 2, "medium", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("heavy cream", 0.5, "cup", "dairy"),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("all-purpose flour", 3, "tbsp", "pantry", True),
        _i("refrigerated pie crust", 1, "count", "grain"),
        _i("fresh thyme", 3, "sprigs", "produce"),
    ], 6, 60, "weekend", nut_free=True, tags=["comfort", "family-favorite", "classic"]),

    _r("AMR-008", "Pork Chops with Apple and Onion", "american", "pork", [
        _i("bone-in pork chops", 4, "count", "protein"),
        _i("apples", 2, "count", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("apple cider vinegar", 1, "tbsp", "pantry", True),
        _i("fresh thyme", 3, "sprigs", "produce"),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("mashed potatoes", 4, "servings", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["classic", "comfort", "seasonal"]),

    _r("AMR-009", "Shrimp and Grits", "american", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("stone-ground grits", 1, "cup", "grain"),
        _i("bacon", 4, "strips", "protein"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("green onions", 4, "stalks", "produce"),
        _i("bell pepper", 1, "count", "produce"),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("heavy cream", 0.5, "cup", "dairy"),
        _i("cheddar cheese", 1, "cup", "dairy"),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("hot sauce", 1, "tsp", "pantry", True),
        _i("lemon", 1, "count", "produce"),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["southern-classic", "comfort", "crowd-pleaser"]),

    _r("AMR-010", "BBQ Chicken Thighs with Slaw", "american", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("BBQ sauce", 1, "cup", "pantry"),
        _i("coleslaw mix", 1, "bag", "produce"),
        _i("apple cider vinegar", 2, "tbsp", "pantry", True),
        _i("mayonnaise", 3, "tbsp", "pantry", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("garlic powder", 0.5, "tsp", "spice", True),
        _i("corn on the cob", 4, "count", "produce"),
        _i("butter", 2, "tbsp", "dairy", True),
    ], 4, 40, "weeknight", gf=True, df=False, nut_free=True, tags=["summer", "crowd-pleaser", "classic"]),

    _r("AMR-011", "Beef Stroganoff", "american", "beef", [
        _i("beef sirloin strips", 1.5, "lbs", "protein"),
        _i("cremini mushrooms", 8, "oz", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("beef broth", 1, "cup", "canned", True),
        _i("sour cream", 1, "cup", "dairy"),
        _i("Dijon mustard", 1, "tbsp", "pantry", True),
        _i("Worcestershire sauce", 1, "tsp", "pantry", True),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("all-purpose flour", 2, "tbsp", "pantry", True),
        _i("egg noodles", 12, "oz", "grain"),
        _i("fresh parsley", 0.25, "cup", "produce"),
    ], 4, 35, "weeknight", nut_free=True, tags=["classic", "comfort", "family-favorite"]),

    _r("AMR-012", "Chicken and Rice Casserole", "american", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("long grain rice", 1.5, "cups", "grain"),
        _i("cream of mushroom soup", 10.5, "oz", "canned"),
        _i("chicken broth", 1.5, "cups", "canned", True),
        _i("frozen peas", 1, "cup", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("cheddar cheese", 1, "cup", "dairy"),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("smoked paprika", 0.5, "tsp", "spice", True),
    ], 6, 60, "weekend", nut_free=True, tags=["casserole", "comfort", "family-favorite", "batch-friendly"]),

    _r("AMR-013", "Classic Beef Burgers", "american", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("brioche buns", 4, "count", "grain"),
        _i("cheddar cheese", 4, "slices", "dairy"),
        _i("romaine lettuce", 4, "leaves", "produce"),
        _i("tomato", 1, "large", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("pickles", 0.5, "cup", "pantry", True),
        _i("ketchup", 2, "tbsp", "pantry", True),
        _i("mustard", 1, "tbsp", "pantry", True),
        _i("mayonnaise", 2, "tbsp", "pantry", True),
        _i("french fries", 1, "lb", "produce"),
    ], 4, 25, "weeknight", nut_free=True, tags=["classic", "crowd-pleaser", "summer"]),

    _r("AMR-014", "Turkey Chili", "american", "turkey", [
        _i("ground turkey", 1.5, "lbs", "protein"),
        _i("kidney beans", 30, "oz", "canned", True),
        _i("diced tomatoes", 28, "oz", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("bell pepper", 1, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("chili powder", 2, "tbsp", "spice", True),
        _i("cumin", 1, "tsp", "spice", True),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("cheddar cheese", 1, "cup", "dairy"),
        _i("sour cream", 0.5, "cup", "dairy"),
    ], 6, 40, "weeknight", gf=True, nut_free=True, tags=["lighter-version", "batch-friendly", "comfort"]),

    _r("AMR-015", "Pork Tenderloin with Mustard Pan Sauce", "american", "pork", [
        _i("pork tenderloin", 1.5, "lbs", "protein"),
        _i("Dijon mustard", 2, "tbsp", "pantry", True),
        _i("whole grain mustard", 1, "tbsp", "pantry", True),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("heavy cream", 0.25, "cup", "dairy"),
        _i("fresh thyme", 3, "sprigs", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("green beans", 1, "lb", "produce"),
        _i("roasted potatoes", 1, "lb", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["elegant", "weeknight-special"]),

    _r("AMR-016", "Salmon Patties", "american", "salmon", [
        _i("canned salmon", 30, "oz", "protein"),
        _i("breadcrumbs", 0.75, "cup", "grain", True),
        _i("egg", 2, "count", "dairy", True),
        _i("green onions", 3, "stalks", "produce"),
        _i("lemon", 1, "count", "produce"),
        _i("Dijon mustard", 1, "tbsp", "pantry", True),
        _i("mayonnaise", 3, "tbsp", "pantry", True),
        _i("old bay seasoning", 1, "tsp", "spice", True),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("coleslaw mix", 1, "bag", "produce"),
        _i("hamburger buns", 4, "count", "grain"),
    ], 4, 25, "weeknight", nut_free=True, tags=["budget", "quick", "classic"]),

    _r("AMR-017", "Beef Shepherd's Pie", "american", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("russet potatoes", 2, "lbs", "produce"),
        _i("frozen peas and carrots", 1.5, "cups", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("beef broth", 0.5, "cup", "canned", True),
        _i("tomato paste", 1, "tbsp", "canned", True),
        _i("Worcestershire sauce", 1, "tbsp", "pantry", True),
        _i("butter", 4, "tbsp", "dairy", True),
        _i("whole milk", 0.5, "cup", "dairy"),
        _i("cheddar cheese", 1, "cup", "dairy"),
        _i("olive oil", 1, "tbsp", "pantry", True),
    ], 6, 60, "weekend", nut_free=True, tags=["comfort", "family-favorite", "batch-friendly"]),

    _r("AMR-018", "Classic Chicken Noodle Soup", "american", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("chicken broth", 48, "oz", "canned", True),
        _i("egg noodles", 3, "cups", "grain"),
        _i("carrots", 3, "medium", "produce"),
        _i("celery", 3, "stalks", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh thyme", 3, "sprigs", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("bay leaves", 2, "count", "spice", True),
        _i("butter", 1, "tbsp", "dairy", True),
    ], 6, 40, "weeknight", nut_free=True, tags=["classic", "comfort", "soup", "batch-friendly"]),

    _r("AMR-019", "Pulled Chicken Sandwiches", "american", "chicken", [
        _i("chicken breast", 2, "lbs", "protein"),
        _i("BBQ sauce", 1, "cup", "pantry"),
        _i("chicken broth", 0.5, "cup", "canned", True),
        _i("apple cider vinegar", 2, "tbsp", "pantry", True),
        _i("brown sugar", 1, "tbsp", "pantry", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("garlic powder", 0.5, "tsp", "spice", True),
        _i("brioche buns", 6, "count", "grain"),
        _i("coleslaw mix", 1, "bag", "produce"),
        _i("mayonnaise", 3, "tbsp", "pantry", True),
        _i("pickles", 0.5, "cup", "pantry", True),
    ], 6, 40, "weeknight", nut_free=True, tags=["crowd-pleaser", "batch-friendly"]),

    _r("AMR-020", "Lamb Chops with Herb Crust", "american", "lamb", [
        _i("lamb loin chops", 8, "count", "protein"),
        _i("fresh rosemary", 2, "tbsp", "produce"),
        _i("fresh thyme", 1, "tbsp", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("Dijon mustard", 2, "tbsp", "pantry", True),
        _i("breadcrumbs", 0.25, "cup", "grain", True),
        _i("Parmesan cheese", 0.25, "cup", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("asparagus", 1, "lb", "produce"),
        _i("roasted potatoes", 1, "lb", "produce"),
    ], 4, 30, "weekend", nut_free=True, tags=["special-occasion", "elegant"]),

    _r("AMR-021", "Salmon with Honey Mustard Glaze", "american", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("honey", 2, "tbsp", "pantry", True),
        _i("Dijon mustard", 2, "tbsp", "pantry", True),
        _i("garlic", 2, "cloves", "produce", True),
        _i("lemon", 1, "count", "produce"),
        _i("fresh thyme", 3, "sprigs", "produce"),
        _i("asparagus", 1, "lb", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("cooked rice", 2, "cups", "grain"),
    ], 4, 25, "weeknight", gf=True, df=True, nut_free=True, tags=["healthy", "quick", "family-friendly"]),

    _r("AMR-022", "One-Pot Cheesy Chicken Mac", "american", "chicken", [
        _i("chicken breast", 1, "lb", "protein"),
        _i("elbow macaroni", 12, "oz", "grain"),
        _i("chicken broth", 3, "cups", "canned", True),
        _i("whole milk", 1, "cup", "dairy"),
        _i("cheddar cheese", 2, "cups", "dairy"),
        _i("cream cheese", 4, "oz", "dairy"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("white onion", 1, "medium", "produce"),
        _i("smoked paprika", 0.5, "tsp", "spice", True),
        _i("Dijon mustard", 1, "tsp", "pantry", True),
        _i("butter", 2, "tbsp", "dairy", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["one-pot", "comfort", "family-favorite", "kid-friendly"]),

    _r("AMR-023", "Pork Baby Back Ribs Oven-Baked", "american", "pork", [
        _i("pork baby back ribs", 2, "racks", "protein"),
        _i("BBQ sauce", 1.5, "cups", "pantry"),
        _i("smoked paprika", 1, "tbsp", "spice", True),
        _i("brown sugar", 2, "tbsp", "pantry", True),
        _i("garlic powder", 1, "tsp", "spice", True),
        _i("cumin", 0.5, "tsp", "spice", True),
        _i("apple cider vinegar", 2, "tbsp", "pantry", True),
        _i("corn on the cob", 4, "count", "produce"),
        _i("coleslaw mix", 1, "bag", "produce"),
    ], 4, 180, "weekend", gf=True, df=False, nut_free=True, tags=["weekend-project", "crowd-pleaser", "summer"]),

    _r("AMR-024", "Shrimp Pasta Primavera", "american", "shrimp", [
        _i("shrimp", 1, "lb", "protein"),
        _i("penne pasta", 12, "oz", "grain"),
        _i("zucchini", 2, "medium", "produce"),
        _i("bell pepper", 1, "count", "produce"),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("fresh spinach", 2, "cups", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("heavy cream", 0.5, "cup", "dairy"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("lemon", 1, "count", "produce"),
        _i("fresh basil", 0.5, "cup", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["light", "fresh", "spring-summer"]),

    _r("AMR-025", "Chicken and Vegetable Soup", "american", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("chicken broth", 48, "oz", "canned", True),
        _i("potatoes", 2, "medium", "produce"),
        _i("carrots", 3, "medium", "produce"),
        _i("celery", 3, "stalks", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("zucchini", 1, "medium", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("dried thyme", 1, "tsp", "spice", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 6, 40, "weeknight", gf=True, df=True, nut_free=True, tags=["healthy", "soup", "batch-friendly"]),

    _r("AMR-026", "Beef Taco Bowl Salad", "american", "beef", [
        _i("ground beef", 1, "lb", "protein"),
        _i("romaine lettuce", 1, "large head", "produce"),
        _i("corn", 1, "cup", "produce"),
        _i("black beans", 15, "oz", "canned", True),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("cheddar cheese", 0.75, "cup", "dairy"),
        _i("avocado", 2, "count", "produce"),
        _i("tortilla chips", 2, "cups", "grain"),
        _i("sour cream", 0.5, "cup", "dairy"),
        _i("lime", 2, "count", "produce"),
        _i("chili powder", 1, "tsp", "spice", True),
        _i("cumin", 0.5, "tsp", "spice", True),
    ], 4, 25, "weeknight", gf=True, nut_free=True, tags=["quick", "crowd-pleaser", "light"]),

    _r("AMR-027", "Pork Schnitzel with Egg Noodles", "american", "pork", [
        _i("pork cutlets", 1.5, "lbs", "protein"),
        _i("breadcrumbs", 1.5, "cups", "grain", True),
        _i("egg", 2, "count", "dairy", True),
        _i("all-purpose flour", 0.5, "cup", "pantry", True),
        _i("lemon", 2, "count", "produce"),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("egg noodles", 12, "oz", "grain"),
        _i("capers", 2, "tbsp", "canned", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("vegetable oil", 0.5, "cup", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["crispy", "classic", "quick"]),

    _r("AMR-028", "Vegetable Pot Pie", "american", "eggs", [
        _i("eggs", 2, "count", "protein"),
        _i("refrigerated pie crust", 2, "count", "grain"),
        _i("frozen peas and carrots", 1.5, "cups", "produce"),
        _i("potatoes", 2, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 2, "cloves", "produce", True),
        _i("vegetable broth", 1.5, "cups", "canned", True),
        _i("heavy cream", 0.5, "cup", "dairy"),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("all-purpose flour", 3, "tbsp", "pantry", True),
        _i("fresh thyme", 2, "sprigs", "produce"),
    ], 6, 70, "weekend", veg=True, nut_free=True, tags=["vegetarian", "comfort", "classic"]),

    _r("AMR-029", "Honey Garlic Chicken Thighs", "american", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("honey", 3, "tbsp", "pantry", True),
        _i("garlic", 6, "cloves", "produce", True),
        _i("soy sauce", 2, "tbsp", "pantry", True),
        _i("apple cider vinegar", 1, "tbsp", "pantry", True),
        _i("butter", 2, "tbsp", "dairy", True),
        _i("fresh thyme", 3, "sprigs", "produce"),
        _i("broccoli", 1, "head", "produce"),
        _i("cooked rice", 2, "cups", "grain"),
        _i("olive oil", 1, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["crowd-pleaser", "sticky-sweet", "quick"]),

    _r("AMR-030", "Beef and Vegetable Stew", "american", "beef", [
        _i("beef stew meat", 2, "lbs", "protein"),
        _i("potatoes", 1.5, "lbs", "produce"),
        _i("carrots", 3, "medium", "produce"),
        _i("celery", 2, "stalks", "produce"),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("beef broth", 3, "cups", "canned", True),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("tomato paste", 2, "tbsp", "canned", True),
        _i("Worcestershire sauce", 1, "tbsp", "pantry", True),
        _i("fresh thyme", 3, "sprigs", "produce"),
        _i("all-purpose flour", 2, "tbsp", "pantry", True),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 6, 90, "weekend", df=True, nut_free=True, tags=["comfort", "batch-friendly", "slow-cook"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# MEDITERRANEAN  (MED-001 → MED-030)
# ─────────────────────────────────────────────────────────────────────────────
MEDITERRANEAN = [
    _r("MED-001", "Chicken Souvlaki Bowls", "mediterranean", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("lemon", 2, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh oregano", 2, "tbsp", "produce"),
        _i("cucumber", 1, "large", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("cooked rice or pita bread", 4, "servings", "grain"),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["fresh", "healthy", "crowd-pleaser"]),

    _r("MED-002", "Lamb Kofta with Tzatziki", "mediterranean", "lamb", [
        _i("ground lamb", 1.5, "lbs", "protein"),
        _i("plain Greek yogurt", 1, "cup", "dairy"),
        _i("cucumber", 1, "medium", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh mint", 0.25, "cup", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("coriander", 1, "tsp", "spice", True),
        _i("cinnamon", 0.25, "tsp", "spice", True),
        _i("lemon", 1, "count", "produce"),
        _i("pita bread", 4, "count", "grain"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["crowd-pleaser", "fresh", "grillable"]),

    _r("MED-003", "Shakshuka", "mediterranean", "eggs", [
        _i("eggs", 6, "count", "protein"),
        _i("crushed tomatoes", 28, "oz", "canned", True),
        _i("bell peppers", 2, "count", "produce"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("harissa paste", 1, "tbsp", "pantry"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("crusty bread", 1, "loaf", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=False, veg=True, nut_free=True, tags=["vegetarian", "bold-flavors", "brunch-style"]),

    _r("MED-004", "Beef Gyro Bowls", "mediterranean", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("cucumber", 1, "large", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("romaine lettuce", 1, "head", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh mint", 2, "tbsp", "produce"),
        _i("lemon", 2, "count", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("pita bread", 4, "count", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["fresh", "crowd-pleaser", "quick"]),

    _r("MED-005", "Salmon with Chermoula", "mediterranean", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("fresh cilantro", 1, "cup", "produce"),
        _i("fresh parsley", 0.5, "cup", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("lemon", 2, "count", "produce"),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("harissa paste", 1, "tbsp", "pantry"),
        _i("olive oil", 4, "tbsp", "pantry", True),
        _i("couscous", 1.5, "cups", "grain"),
        _i("cherry tomatoes", 1, "cup", "produce"),
    ], 4, 30, "weeknight", df=True, nut_free=True, tags=["bold-flavors", "healthy", "North African"]),

    _r("MED-006", "Chicken Shawarma Bowls", "mediterranean", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("plain Greek yogurt", 0.5, "cup", "dairy"),
        _i("lemon", 2, "count", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("coriander", 1, "tsp", "spice", True),
        _i("turmeric", 0.5, "tsp", "spice", True),
        _i("smoked paprika", 1, "tsp", "spice", True),
        _i("cinnamon", 0.25, "tsp", "spice", True),
        _i("cooked rice or pita", 4, "servings", "grain"),
        _i("cucumber", 1, "large", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["bold-flavors", "crowd-pleaser", "meal-prep"]),

    _r("MED-007", "Moroccan Chicken Tagine", "mediterranean", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("diced tomatoes", 14, "oz", "canned", True),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh ginger", 1, "tbsp", "produce", True),
        _i("preserved lemon", 1, "count", "pantry"),
        _i("green olives", 0.5, "cup", "canned", True),
        _i("ras el hanout", 2, "tsp", "spice", True),
        _i("turmeric", 0.5, "tsp", "spice", True),
        _i("cinnamon", 0.25, "tsp", "spice", True),
        _i("fresh cilantro", 0.5, "cup", "produce"),
        _i("couscous", 1.5, "cups", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 55, "weekend", gf=True, df=True, nut_free=True, tags=["bold-flavors", "North African", "comfort"]),

    _r("MED-008", "Turkish Lamb and Eggplant", "mediterranean", "lamb", [
        _i("ground lamb", 1.5, "lbs", "protein"),
        _i("eggplant", 2, "medium", "produce"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("coriander", 1, "tsp", "spice", True),
        _i("cinnamon", 0.5, "tsp", "spice", True),
        _i("fresh mint", 0.25, "cup", "produce"),
        _i("plain Greek yogurt", 0.5, "cup", "dairy"),
        _i("cooked rice", 2, "cups", "grain"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 45, "weekend", gf=True, nut_free=True, tags=["bold-flavors", "comfort", "Turkish"]),

    _r("MED-009", "Pork Souvlaki Skewers", "mediterranean", "pork", [
        _i("pork tenderloin", 1.5, "lbs", "protein"),
        _i("lemon", 2, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh oregano", 2, "tbsp", "produce"),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("cucumber", 1, "medium", "produce"),
        _i("fresh mint", 2, "tbsp", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("pita bread", 4, "count", "grain"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["grillable", "fresh", "summer"]),

    _r("MED-010", "Shrimp Saganaki", "mediterranean", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("feta cheese", 6, "oz", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("fresh oregano", 1, "tbsp", "produce"),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("crusty bread", 1, "loaf", "grain"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=False, nut_free=True, tags=["Greek", "bold-flavors", "quick"]),

    _r("MED-011", "Chicken Harissa Grain Bowls", "mediterranean", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("harissa paste", 3, "tbsp", "pantry"),
        _i("cooked farro or quinoa", 2, "cups", "grain"),
        _i("chickpeas", 15, "oz", "canned", True),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("cucumber", 1, "medium", "produce"),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("lemon", 2, "count", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
        _i("plain Greek yogurt", 0.5, "cup", "dairy"),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["healthy", "meal-prep", "bold-flavors"]),

    _r("MED-012", "Israeli Couscous with Chicken", "mediterranean", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("Israeli couscous", 1.5, "cups", "grain"),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("chicken broth", 2, "cups", "canned", True),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("lemon", 1, "count", "produce"),
        _i("fresh basil", 0.5, "cup", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["fresh", "one-pot", "Mediterranean"]),

    _r("MED-013", "Falafel Bowls", "mediterranean", "eggs", [
        _i("eggs", 2, "count", "protein"),
        _i("canned chickpeas", 30, "oz", "canned", True),
        _i("plain Greek yogurt", 1, "cup", "dairy"),
        _i("cucumber", 1, "large", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("romaine lettuce", 1, "head", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("pita bread", 4, "count", "grain"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("coriander", 1, "tsp", "spice", True),
        _i("fresh parsley", 0.5, "cup", "produce"),
        _i("fresh mint", 2, "tbsp", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 40, "weeknight", veg=True, nut_free=True, tags=["vegetarian", "fresh", "crowd-pleaser"]),

    _r("MED-014", "Turkey Kofta Flatbreads", "mediterranean", "turkey", [
        _i("ground turkey", 1.5, "lbs", "protein"),
        _i("pita flatbread", 4, "count", "grain"),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("cucumber", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh mint", 0.25, "cup", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("coriander", 1, "tsp", "spice", True),
        _i("cinnamon", 0.25, "tsp", "spice", True),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("lemon", 1, "count", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["lighter-version", "fresh", "crowd-pleaser"]),

    _r("MED-015", "Beef Kafta Bowls", "mediterranean", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("cooked rice or bulgur", 2, "cups", "grain"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh parsley", 0.5, "cup", "produce"),
        _i("cumin", 1.5, "tsp", "spice", True),
        _i("coriander", 1, "tsp", "spice", True),
        _i("cinnamon", 0.25, "tsp", "spice", True),
        _i("allspice", 0.25, "tsp", "spice", True),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("cucumber", 1, "medium", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("lemon", 1, "count", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", gf=True, nut_free=True, tags=["bold-flavors", "fresh", "Lebanese"]),

    _r("MED-016", "Greek Lemon Chicken with Orzo", "mediterranean", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("orzo pasta", 1.5, "cups", "grain"),
        _i("lemon", 3, "count", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("chicken broth", 2.5, "cups", "canned", True),
        _i("fresh oregano", 2, "tbsp", "produce"),
        _i("fresh spinach", 2, "cups", "produce"),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 40, "weeknight", nut_free=True, tags=["one-pot", "comfort", "Greek"]),

    _r("MED-017", "Lamb Gyro Bowls", "mediterranean", "lamb", [
        _i("lamb leg steaks", 1.5, "lbs", "protein"),
        _i("plain Greek yogurt", 1, "cup", "dairy"),
        _i("cucumber", 1, "large", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("lemon", 2, "count", "produce"),
        _i("fresh mint", 0.25, "cup", "produce"),
        _i("fresh dill", 2, "tbsp", "produce"),
        _i("romaine lettuce", 1, "head", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("pita bread", 4, "count", "grain"),
        _i("dried oregano", 1, "tsp", "spice", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", nut_free=True, tags=["fresh", "crowd-pleaser", "Greek"]),

    _r("MED-018", "Shrimp with Feta and Tomatoes", "mediterranean", "shrimp", [
        _i("shrimp", 1.25, "lbs", "protein"),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("feta cheese", 6, "oz", "dairy"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("lemon", 1, "count", "produce"),
        _i("fresh oregano", 1, "tbsp", "produce"),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("crusty bread", 1, "loaf", "grain"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 25, "weeknight", gf=False, nut_free=True, tags=["quick", "fresh", "elegant"]),

    _r("MED-019", "Chicken and Chickpea Stew", "mediterranean", "chicken", [
        _i("chicken thighs", 1.5, "lbs", "protein"),
        _i("chickpeas", 30, "oz", "canned", True),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("ras el hanout", 1.5, "tsp", "spice", True),
        _i("smoked paprika", 0.5, "tsp", "spice", True),
        _i("lemon", 1, "count", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("couscous", 1.5, "cups", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 40, "weeknight", gf=True, df=True, nut_free=True, tags=["healthy", "batch-friendly", "comfort"]),

    _r("MED-020", "Pork with Capers and Green Olives", "mediterranean", "pork", [
        _i("pork loin chops", 1.5, "lbs", "protein"),
        _i("green olives", 0.5, "cup", "canned", True),
        _i("capers", 2, "tbsp", "canned", True),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("dry white wine", 0.5, "cup", "pantry", True),
        _i("fresh rosemary", 2, "sprigs", "produce"),
        _i("lemon", 1, "count", "produce"),
        _i("orzo pasta", 1.5, "cups", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 35, "weeknight", df=True, nut_free=True, tags=["bold-flavors", "Italian-Greek"]),

    _r("MED-021", "Salmon Tzatziki Bowls", "mediterranean", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("plain Greek yogurt", 1, "cup", "dairy"),
        _i("cucumber", 1, "large", "produce"),
        _i("garlic", 3, "cloves", "produce", True),
        _i("fresh dill", 2, "tbsp", "produce"),
        _i("lemon", 2, "count", "produce"),
        _i("cooked farro or quinoa", 2, "cups", "grain"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=True, nut_free=True, tags=["healthy", "fresh", "light"]),

    _r("MED-022", "Chicken Tagine with Preserved Lemon", "mediterranean", "chicken", [
        _i("chicken thighs", 2, "lbs", "protein"),
        _i("preserved lemon", 2, "count", "pantry"),
        _i("green olives", 0.5, "cup", "canned", True),
        _i("chicken broth", 1, "cup", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("saffron", 0.25, "tsp", "spice", True),
        _i("ginger", 1, "tsp", "spice", True),
        _i("turmeric", 0.5, "tsp", "spice", True),
        _i("fresh cilantro", 0.5, "cup", "produce"),
        _i("couscous", 1.5, "cups", "grain"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 55, "weekend", gf=True, df=True, nut_free=True, tags=["Moroccan", "special-occasion", "bold-flavors"]),

    _r("MED-023", "Mediterranean Baked Cod", "mediterranean", "salmon", [
        _i("cod fillets", 1.5, "lbs", "protein"),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("kalamata olives", 0.5, "cup", "canned", True),
        _i("capers", 2, "tbsp", "canned", True),
        _i("garlic", 4, "cloves", "produce", True),
        _i("lemon", 2, "count", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("red pepper flakes", 0.5, "tsp", "spice", True),
        _i("white wine", 0.25, "cup", "pantry", True),
        _i("couscous", 1.5, "cups", "grain"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", gf=True, df=True, nut_free=True, tags=["healthy", "light", "quick"]),

    _r("MED-024", "Turkey and Spinach Stuffed Peppers", "mediterranean", "turkey", [
        _i("ground turkey", 1, "lb", "protein"),
        _i("bell peppers", 4, "count", "produce"),
        _i("cooked rice", 1, "cup", "grain"),
        _i("fresh spinach", 3, "cups", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("garlic", 3, "cloves", "produce", True),
        _i("white onion", 1, "medium", "produce"),
        _i("cumin", 0.5, "tsp", "spice", True),
        _i("dried oregano", 0.5, "tsp", "spice", True),
        _i("lemon", 1, "count", "produce"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 50, "weekend", gf=True, nut_free=True, tags=["healthy", "lighter-version", "meal-prep"]),

    _r("MED-025", "Seafood Paella-Style Rice", "mediterranean", "shrimp", [
        _i("shrimp", 0.75, "lb", "protein"),
        _i("mussels or clams", 1, "lb", "protein"),
        _i("Bomba or short-grain rice", 1.5, "cups", "grain"),
        _i("chicken broth", 3, "cups", "canned", True),
        _i("saffron", 0.25, "tsp", "spice", True),
        _i("white onion", 1, "medium", "produce"),
        _i("bell peppers", 2, "count", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("smoked paprika", 1.5, "tsp", "spice", True),
        _i("lemon", 2, "count", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 50, "weekend", gf=True, df=True, nut_free=True, tags=["special-occasion", "Spanish", "seafood"]),

    _r("MED-026", "Beef Moussaka-Style Casserole", "mediterranean", "beef", [
        _i("ground beef", 1.5, "lbs", "protein"),
        _i("eggplant", 2, "large", "produce"),
        _i("crushed tomatoes", 14, "oz", "canned", True),
        _i("white onion", 1, "large", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("whole milk", 1.5, "cups", "dairy"),
        _i("butter", 3, "tbsp", "dairy", True),
        _i("all-purpose flour", 3, "tbsp", "pantry", True),
        _i("Parmesan cheese", 0.5, "cup", "dairy"),
        _i("egg", 1, "count", "dairy", True),
        _i("cinnamon", 0.5, "tsp", "spice", True),
        _i("allspice", 0.25, "tsp", "spice", True),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 6, 75, "weekend", nut_free=True, tags=["Greek", "comfort", "special-occasion"]),

    _r("MED-027", "Chicken Za'atar Flatbreads", "mediterranean", "chicken", [
        _i("chicken breast", 1.5, "lbs", "protein"),
        _i("pita flatbread", 4, "count", "grain"),
        _i("za'atar spice blend", 2, "tbsp", "spice"),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("cucumber", 1, "medium", "produce"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("fresh mint", 0.25, "cup", "produce"),
        _i("lemon", 2, "count", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["quick", "fresh", "Levantine"]),

    _r("MED-028", "Pork Gyros with Pita", "mediterranean", "pork", [
        _i("pork shoulder", 1.5, "lbs", "protein"),
        _i("pita bread", 6, "count", "grain"),
        _i("plain Greek yogurt", 1, "cup", "dairy"),
        _i("cucumber", 1, "large", "produce"),
        _i("garlic", 5, "cloves", "produce", True),
        _i("fresh mint", 2, "tbsp", "produce"),
        _i("lemon", 2, "count", "produce"),
        _i("dried oregano", 2, "tsp", "spice", True),
        _i("cumin", 0.5, "tsp", "spice", True),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("olive oil", 3, "tbsp", "pantry", True),
    ], 4, 40, "weekend", nut_free=True, tags=["crowd-pleaser", "Greek", "weekend"]),

    _r("MED-029", "Lamb Flatbread Pizzas", "mediterranean", "lamb", [
        _i("ground lamb", 1, "lb", "protein"),
        _i("flatbread or naan", 4, "count", "grain"),
        _i("plain Greek yogurt", 0.75, "cup", "dairy"),
        _i("white onion", 1, "medium", "produce"),
        _i("garlic", 4, "cloves", "produce", True),
        _i("fresh mint", 0.25, "cup", "produce"),
        _i("fresh parsley", 0.25, "cup", "produce"),
        _i("cumin", 1, "tsp", "spice", True),
        _i("coriander", 0.5, "tsp", "spice", True),
        _i("pine nuts", 3, "tbsp", "pantry"),
        _i("cherry tomatoes", 1, "cup", "produce"),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("olive oil", 2, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=False, tags=["Turkish", "fun", "crowd-pleaser"]),

    _r("MED-030", "Salmon and Tabbouleh Bowls", "mediterranean", "salmon", [
        _i("salmon fillets", 1.5, "lbs", "protein"),
        _i("bulgur wheat", 1.5, "cups", "grain"),
        _i("fresh parsley", 2, "bunches", "produce"),
        _i("fresh mint", 0.5, "cup", "produce"),
        _i("cherry tomatoes", 2, "cups", "produce"),
        _i("cucumber", 1, "large", "produce"),
        _i("red onion", 0.5, "medium", "produce"),
        _i("lemon", 3, "count", "produce"),
        _i("garlic", 2, "cloves", "produce", True),
        _i("feta cheese", 4, "oz", "dairy"),
        _i("olive oil", 4, "tbsp", "pantry", True),
    ], 4, 30, "weeknight", nut_free=True, tags=["healthy", "fresh", "light", "Lebanese"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# MASTER INDEX
# ─────────────────────────────────────────────────────────────────────────────

# ALL_RECIPES and plant-based collections are assembled at end of file.
# _BY_ID is populated there too, after all lists are defined.
# CUISINE_TYPES / PROTEIN_TYPES available immediately for imports.

_BY_ID: dict[str, dict] = {}   # populated at module end — do not use before then

CUISINE_TYPES = ["mexican", "italian", "asian", "american", "mediterranean"]
PROTEIN_TYPES = ["chicken", "beef", "pork", "turkey", "shrimp", "salmon",
                 "lamb", "eggs", "legumes", "tofu", "jackfruit"]


# ─────────────────────────────────────────────────────────────────────────────
# QUERY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_recipe(recipe_id: str) -> Optional[dict]:
    """Fetch a single recipe by ID."""
    return _BY_ID.get(recipe_id)


def query_recipes(
    proteins: Optional[list] = None,
    cuisines: Optional[list] = None,
    dietary_flags: Optional[dict] = None,
    exclude_ids: Optional[list] = None,
    complexity: Optional[str] = None,
    tags: Optional[list] = None,
    max_results: int = 20,
) -> list[dict]:
    """
    Query the recipe library with filters.

    proteins       — list of protein types, e.g. ["chicken", "beef"]
    cuisines       — list of cuisine keys, e.g. ["mexican", "italian"]
    dietary_flags  — dict of required True flags, e.g. {"gluten_free": True}
    exclude_ids    — list of recipe IDs to skip (recency window)
    complexity     — "weeknight", "weekend", or "batch"
    tags           — list of tag strings (OR match — any tag matches)
    max_results    — cap on returned results
    """
    results = []
    exclude = set(exclude_ids or [])

    for recipe in ALL_RECIPES:
        if recipe["id"] in exclude:
            continue
        if proteins and recipe["primary_protein"] not in [p.lower() for p in proteins]:
            continue
        if cuisines and recipe["cuisine"] not in [c.lower() for c in cuisines]:
            continue
        if dietary_flags:
            flags = recipe["dietary_flags"]
            if not all(flags.get(k) == v for k, v in dietary_flags.items()):
                continue
        if complexity and recipe["complexity"] != complexity:
            continue
        if tags and not any(t in recipe.get("tags", []) for t in tags):
            continue
        results.append(recipe)
        if len(results) >= max_results:
            break

    return results


def recipes_for_sale_items(
    sale_item_names: list,
    proteins: Optional[list] = None,
    cuisines: Optional[list] = None,
    dietary_flags: Optional[dict] = None,
    exclude_ids: Optional[list] = None,
) -> list[dict]:
    """
    Find recipes whose primary protein matches available sale items.

    sale_item_names — list of ingredient name strings from the flyer
    proteins        — optional additional protein type filter
    cuisines        — optional cuisine filter
    dietary_flags   — dietary restriction flags
    exclude_ids     — recently used recipe IDs (4-week recency window)

    POC: matches on simple string containment. Phase 2: fuzzy match + USDA FDC mapping.
    """
    # Determine which protein types are present in the sale items
    matched_proteins = set()
    name_blob = " ".join(sale_item_names).lower()

    protein_keywords = {
        "chicken":  ["chicken"],
        "beef":     ["beef", "steak", "ground beef", "chuck", "brisket", "sirloin", "ribeye",
                     "flank", "skirt", "short rib"],
        "pork":     ["pork", "ham", "bacon", "sausage", "chorizo", "prosciutto", "tenderloin"],
        "turkey":   ["turkey"],
        "shrimp":   ["shrimp", "prawn"],
        "salmon":   ["salmon", "cod", "tilapia", "halibut", "fish fillet", "fish", "tuna",
                     "trout", "mahi", "scallop", "crab"],
        "lamb":     ["lamb"],
        "eggs":     ["egg", "eggs"],
        # Plant proteins — match vegan/vegetarian and pescatarian recipes
        "legumes":  ["chickpea", "lentil", "black bean", "white bean", "kidney bean",
                     "edamame", "bean"],
        "tofu":     ["tofu", "tempeh", "seitan"],
        "jackfruit":["jackfruit"],
    }

    for ptype, keywords in protein_keywords.items():
        if any(kw in name_blob for kw in keywords):
            matched_proteins.add(ptype)

    # Layer with explicit protein preferences if provided
    if proteins:
        matched_proteins = matched_proteins & {p.lower() for p in proteins}
        # If intersection is empty, fall back to sale matches only
        if not matched_proteins:
            pass  # fall back handled by returning all matched below


# =============================================================================
# VEGAN RECIPES  (VGN-MEX-* · VGN-ITA-* · VGN-ASN-* · VGN-AMR-* · VGN-MED-*)
# primary_protein: "tofu" | "legumes" | "jackfruit" | "lentils"
# All tagged vegan=True, veg=True, df=True
# =============================================================================
VEGAN = [
    # ── Mexican Vegan ──────────────────────────────────────────────────────────
    _r("VGN-MEX-001", "Black Bean Tacos with Avocado Crema", "mexican", "legumes", [
        _i("canned black beans",  2,   "15oz cans", "legumes"),
        _i("corn tortillas",      12,  "count",      "grain"),
        _i("avocado",             2,   "medium",     "produce"),
        _i("lime",                2,   "count",      "produce"),
        _i("red onion",           1,   "medium",     "produce"),
        _i("cilantro",            1,   "bunch",      "produce"),
        _i("cumin",               1,   "tsp",        "spice",  True),
        _i("chili powder",        1,   "tsp",        "spice",  True),
        _i("olive oil",           1,   "tbsp",       "pantry", True),
    ], 4, 20, "weeknight", gf=True, df=True, veg=True, vegan=True, tags=["quick", "plant-based"]),

    _r("VGN-MEX-002", "Jackfruit Carnitas Bowls", "mexican", "jackfruit", [
        _i("canned jackfruit",    2,   "20oz cans",  "protein"),
        _i("brown rice",          2,   "cups",       "grain"),
        _i("canned black beans",  1,   "15oz can",   "legumes"),
        _i("bell pepper",         2,   "count",      "produce"),
        _i("lime",                2,   "count",      "produce"),
        _i("cumin",               2,   "tsp",        "spice",  True),
        _i("smoked paprika",      1,   "tsp",        "spice",  True),
        _i("olive oil",           2,   "tbsp",       "pantry", True),
    ], 4, 35, "weeknight", gf=True, df=True, veg=True, vegan=True, tags=["plant-based", "meal-prep"]),

    _r("VGN-MEX-003", "Lentil Taco Bowls", "mexican", "lentils", [
        _i("green lentils",       1.5, "cups",       "legumes"),
        _i("corn tortillas",      8,   "count",      "grain"),
        _i("roma tomatoes",       3,   "count",      "produce"),
        _i("red onion",           1,   "medium",     "produce"),
        _i("jalapeño",            1,   "count",      "produce"),
        _i("cilantro",            1,   "bunch",      "produce"),
        _i("lime",                1,   "count",      "produce"),
        _i("cumin",               1,   "tsp",        "spice",  True),
        _i("chili powder",        1.5, "tsp",        "spice",  True),
    ], 4, 30, "weeknight", gf=True, df=True, veg=True, vegan=True, tags=["high-protein", "plant-based"]),

    # ── Italian Vegan ──────────────────────────────────────────────────────────
    _r("VGN-ITA-001", "Chickpea and Tomato Pasta", "italian", "legumes", [
        _i("canned chickpeas",    2,   "15oz cans",  "legumes"),
        _i("pasta",               12,  "oz",         "grain"),
        _i("canned crushed tomatoes", 1, "28oz can", "canned"),
        _i("baby spinach",        3,   "oz",         "produce"),
        _i("garlic",              4,   "cloves",     "produce", True),
        _i("olive oil",           3,   "tbsp",       "pantry",  True),
        _i("dried basil",         1,   "tsp",        "spice",   True),
        _i("red pepper flakes",   0.5, "tsp",        "spice",   True),
    ], 4, 25, "weeknight", df=True, veg=True, vegan=True, tags=["quick", "pantry-friendly"]),

    _r("VGN-ITA-002", "Lentil Bolognese", "italian", "lentils", [
        _i("red lentils",         1.5, "cups",       "legumes"),
        _i("pasta",               12,  "oz",         "grain"),
        _i("canned diced tomatoes",1,  "28oz can",   "canned"),
        _i("carrots",             2,   "medium",     "produce"),
        _i("celery",              2,   "stalks",     "produce"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("dried oregano",       1,   "tsp",        "spice",   True),
        _i("bay leaf",            1,   "count",      "spice",   True),
    ], 4, 40, "weeknight", df=True, veg=True, vegan=True, tags=["hearty", "plant-based"]),

    # ── Asian Vegan ────────────────────────────────────────────────────────────
    _r("VGN-ASN-001", "Crispy Tofu Stir-Fry", "asian", "tofu", [
        _i("firm tofu",           14,  "oz",         "protein"),
        _i("broccoli",            1,   "large head", "produce"),
        _i("bell pepper",         2,   "count",      "produce"),
        _i("snap peas",           6,   "oz",         "produce"),
        _i("brown rice",          2,   "cups",       "grain"),
        _i("soy sauce",           3,   "tbsp",       "pantry",  True),
        _i("sesame oil",          1,   "tbsp",       "pantry",  True),
        _i("cornstarch",          2,   "tbsp",       "pantry",  True),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("ginger",              1,   "tsp",        "spice",   True),
    ], 4, 30, "weeknight", df=True, veg=True, vegan=True, tags=["high-protein", "quick"]),

    _r("VGN-ASN-002", "Edamame Fried Rice", "asian", "legumes", [
        _i("shelled edamame",     12,  "oz",         "legumes"),
        _i("brown rice",          3,   "cups",       "grain"),
        _i("carrots",             2,   "medium",     "produce"),
        _i("green onions",        4,   "stalks",     "produce"),
        _i("frozen corn",         1,   "cup",        "frozen"),
        _i("soy sauce",           3,   "tbsp",       "pantry",  True),
        _i("sesame oil",          2,   "tsp",        "pantry",  True),
        _i("garlic",              2,   "cloves",     "produce", True),
    ], 4, 25, "weeknight", df=True, veg=True, vegan=True, tags=["quick", "meal-prep"]),

    _r("VGN-ASN-003", "Coconut Red Lentil Soup", "asian", "lentils", [
        _i("red lentils",         1.5, "cups",       "legumes"),
        _i("coconut milk",        1,   "13.5oz can", "canned"),
        _i("baby spinach",        3,   "oz",         "produce"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("fresh ginger",        1,   "tbsp",       "produce"),
        _i("curry powder",        2,   "tsp",        "spice",   True),
        _i("turmeric",            0.5, "tsp",        "spice",   True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
    ], 4, 30, "weeknight", gf=True, df=True, veg=True, vegan=True, tags=["cozy", "one-pot"]),

    # ── American Vegan ─────────────────────────────────────────────────────────
    _r("VGN-AMR-001", "White Bean and Kale Soup", "american_comfort", "legumes", [
        _i("canned white beans",  2,   "15oz cans",  "legumes"),
        _i("kale",                1,   "bunch",      "produce"),
        _i("carrots",             3,   "medium",     "produce"),
        _i("celery",              3,   "stalks",     "produce"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("garlic",              4,   "cloves",     "produce", True),
        _i("vegetable broth",     4,   "cups",       "canned",  True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("thyme",               1,   "tsp",        "spice",   True),
    ], 4, 35, "weeknight", gf=True, df=True, veg=True, vegan=True, tags=["cozy", "one-pot"]),

    _r("VGN-AMR-002", "BBQ Jackfruit Sandwiches", "american_comfort", "jackfruit", [
        _i("canned jackfruit",    2,   "20oz cans",  "protein"),
        _i("whole wheat buns",    4,   "count",      "grain"),
        _i("coleslaw mix",        1,   "14oz bag",   "produce"),
        _i("apple cider vinegar", 2,   "tbsp",       "pantry",  True),
        _i("BBQ sauce",           0.5, "cup",        "pantry",  True),
        _i("smoked paprika",      1,   "tsp",        "spice",   True),
        _i("garlic powder",       0.5, "tsp",        "spice",   True),
    ], 4, 30, "weeknight", df=True, veg=True, vegan=True, tags=["comfort", "family-friendly"]),

    # ── Mediterranean Vegan ────────────────────────────────────────────────────
    _r("VGN-MED-001", "Falafel and Tabbouleh Bowls", "mediterranean", "legumes", [
        _i("canned chickpeas",    2,   "15oz cans",  "legumes"),
        _i("bulgur wheat",        1,   "cup",        "grain"),
        _i("parsley",             1,   "large bunch","produce"),
        _i("roma tomatoes",       3,   "count",      "produce"),
        _i("cucumber",            1,   "medium",     "produce"),
        _i("lemon",               2,   "count",      "produce"),
        _i("olive oil",           3,   "tbsp",       "pantry",  True),
        _i("cumin",               1,   "tsp",        "spice",   True),
        _i("coriander",           1,   "tsp",        "spice",   True),
    ], 4, 40, "weeknight", df=True, veg=True, vegan=True, tags=["high-protein", "fresh"]),

    _r("VGN-MED-002", "Shakshuka with Chickpeas", "mediterranean", "legumes", [
        _i("canned chickpeas",    1,   "15oz can",   "legumes"),
        _i("canned diced tomatoes",1,  "28oz can",   "canned"),
        _i("bell pepper",         1,   "count",      "produce"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("smoked paprika",      1,   "tsp",        "spice",   True),
        _i("cumin",               1,   "tsp",        "spice",   True),
        _i("crusty bread",        1,   "loaf",       "grain"),
    ], 4, 25, "weeknight", df=True, veg=True, vegan=True, tags=["one-pan", "cozy"]),
]


# =============================================================================
# VEGETARIAN RECIPES  (VGT-*) — eggs and dairy allowed
# primary_protein: "eggs" | "legumes" | "tofu" | "cheese"
# All tagged veg=True (not necessarily vegan)
# =============================================================================
VEGETARIAN = [
    # ── Mexican Vegetarian ─────────────────────────────────────────────────────
    _r("VGT-MEX-001", "Egg and Black Bean Burritos", "mexican", "eggs", [
        _i("eggs",                8,   "large",      "protein"),
        _i("canned black beans",  1,   "15oz can",   "legumes"),
        _i("flour tortillas",     4,   "large",      "grain"),
        _i("shredded Mexican cheese", 1, "cup",      "dairy"),
        _i("salsa",               0.5, "cup",        "canned",  True),
        _i("cumin",               0.5, "tsp",        "spice",   True),
        _i("olive oil",           1,   "tbsp",       "pantry",  True),
    ], 4, 20, "weeknight", veg=True, tags=["quick", "breakfast-for-dinner"]),

    _r("VGT-MEX-002", "Cheese Enchiladas with Red Sauce", "mexican", "cheese", [
        _i("shredded cheese blend",2,  "cups",       "dairy"),
        _i("corn tortillas",      8,   "count",      "grain"),
        _i("enchilada sauce",     2,   "10oz cans",  "canned"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("sour cream",          0.5, "cup",        "dairy"),
        _i("cilantro",            1,   "bunch",      "produce"),
        _i("olive oil",           1,   "tbsp",       "pantry",  True),
    ], 4, 40, "weeknight", gf=True, veg=True, tags=["comfort", "family-friendly"]),

    # ── Italian Vegetarian ─────────────────────────────────────────────────────
    _r("VGT-ITA-001", "Pasta Primavera with Parmesan", "italian", "cheese", [
        _i("pasta",               12,  "oz",         "grain"),
        _i("zucchini",            2,   "medium",     "produce"),
        _i("cherry tomatoes",     1,   "pint",       "produce"),
        _i("bell pepper",         1,   "count",      "produce"),
        _i("parmesan",            0.75,"cup",        "dairy"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("olive oil",           3,   "tbsp",       "pantry",  True),
        _i("dried basil",         1,   "tsp",        "spice",   True),
    ], 4, 25, "weeknight", veg=True, tags=["quick", "fresh"]),

    _r("VGT-ITA-002", "Margherita Flatbread Pizzas", "italian", "cheese", [
        _i("flatbread or naan",   4,   "count",      "grain"),
        _i("fresh mozzarella",    8,   "oz",         "dairy"),
        _i("roma tomatoes",       3,   "medium",     "produce"),
        _i("fresh basil",         1,   "bunch",      "produce"),
        _i("pizza sauce",         0.5, "cup",        "canned",  True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("garlic powder",       0.5, "tsp",        "spice",   True),
    ], 4, 20, "weeknight", veg=True, tags=["quick", "kid-friendly"]),

    # ── Asian Vegetarian ───────────────────────────────────────────────────────
    _r("VGT-ASN-001", "Tofu and Vegetable Fried Rice", "asian", "tofu", [
        _i("firm tofu",           14,  "oz",         "protein"),
        _i("brown rice",          3,   "cups",       "grain"),
        _i("eggs",                3,   "large",      "protein"),
        _i("frozen peas",         1,   "cup",        "frozen"),
        _i("carrots",             2,   "medium",     "produce"),
        _i("green onions",        4,   "stalks",     "produce"),
        _i("soy sauce",           3,   "tbsp",       "pantry",  True),
        _i("sesame oil",          1,   "tbsp",       "pantry",  True),
    ], 4, 30, "weeknight", df=True, veg=True, tags=["quick", "high-protein"]),

    _r("VGT-ASN-002", "Miso Soup with Tofu and Seaweed", "asian", "tofu", [
        _i("silken tofu",         14,  "oz",         "protein"),
        _i("miso paste",          0.25,"cup",        "pantry",  True),
        _i("dried wakame",        0.25,"cup",        "pantry",  True),
        _i("green onions",        3,   "stalks",     "produce"),
        _i("brown rice",          2,   "cups",       "grain"),
        _i("soy sauce",           1,   "tbsp",       "pantry",  True),
        _i("sesame oil",          1,   "tsp",        "pantry",  True),
    ], 4, 20, "weeknight", df=True, veg=True, tags=["light", "Japanese"]),

    # ── American Vegetarian ────────────────────────────────────────────────────
    _r("VGT-AMR-001", "Vegetarian Chili", "american_comfort", "legumes", [
        _i("canned kidney beans", 2,   "15oz cans",  "legumes"),
        _i("canned black beans",  1,   "15oz can",   "legumes"),
        _i("canned diced tomatoes",1,  "28oz can",   "canned"),
        _i("bell pepper",         2,   "count",      "produce"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("shredded cheddar",    1,   "cup",        "dairy"),
        _i("chili powder",        2,   "tbsp",       "spice",   True),
        _i("cumin",               1,   "tsp",        "spice",   True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
    ], 4, 35, "weeknight", gf=True, veg=True, tags=["hearty", "meal-prep"]),

    _r("VGT-AMR-002", "Caprese Egg Bake", "american_comfort", "eggs", [
        _i("eggs",                8,   "large",      "protein"),
        _i("fresh mozzarella",    6,   "oz",         "dairy"),
        _i("cherry tomatoes",     1,   "pint",       "produce"),
        _i("fresh basil",         1,   "bunch",      "produce"),
        _i("crusty bread",        1,   "loaf",       "grain"),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("garlic",              2,   "cloves",     "produce", True),
    ], 4, 30, "weeknight", gf=False, veg=True, tags=["breakfast-for-dinner", "fresh"]),

    # ── Mediterranean Vegetarian ───────────────────────────────────────────────
    _r("VGT-MED-001", "Greek Egg and Vegetable Skillet", "mediterranean", "eggs", [
        _i("eggs",                8,   "large",      "protein"),
        _i("feta cheese",         4,   "oz",         "dairy"),
        _i("cherry tomatoes",     1,   "pint",       "produce"),
        _i("baby spinach",        3,   "oz",         "produce"),
        _i("kalamata olives",     0.5, "cup",        "pantry",  True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("oregano",             1,   "tsp",        "spice",   True),
        _i("pita bread",          4,   "count",      "grain"),
    ], 4, 20, "weeknight", gf=False, veg=True, tags=["quick", "fresh"]),

    _r("VGT-MED-002", "Spanakopita-Style Pasta", "mediterranean", "cheese", [
        _i("pasta",               12,  "oz",         "grain"),
        _i("frozen spinach",      10,  "oz",         "frozen"),
        _i("feta cheese",         6,   "oz",         "dairy"),
        _i("ricotta",             1,   "cup",        "dairy"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("nutmeg",              0.25,"tsp",        "spice",   True),
        _i("lemon",               1,   "count",      "produce"),
    ], 4, 30, "weeknight", veg=True, tags=["cozy", "Greek-inspired"]),
]


# =============================================================================
# PESCATARIAN RECIPES  (PSC-*) — fish/seafood, no land meat
# primary_protein: "salmon" | "shrimp" | "cod" | "tuna" | "tilapia"
# =============================================================================
PESCATARIAN = [
    # ── Mexican Pescatarian ────────────────────────────────────────────────────
    _r("PSC-MEX-001", "Fish Tacos with Mango Salsa", "mexican", "cod", [
        _i("cod fillets",         1.5, "lbs",        "protein"),
        _i("corn tortillas",      12,  "count",      "grain"),
        _i("mango",               1,   "large",      "produce"),
        _i("red onion",           0.5, "medium",     "produce"),
        _i("jalapeño",            1,   "count",      "produce"),
        _i("cilantro",            1,   "bunch",      "produce"),
        _i("lime",                3,   "count",      "produce"),
        _i("cumin",               1,   "tsp",        "spice",   True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["fresh", "summer"]),

    _r("PSC-MEX-002", "Shrimp Fajita Bowls", "mexican", "shrimp", [
        _i("shrimp",              1.5, "lbs",        "protein"),
        _i("bell peppers",        3,   "count",      "produce"),
        _i("white onion",         1,   "large",      "produce"),
        _i("brown rice",          2,   "cups",       "grain"),
        _i("lime",                2,   "count",      "produce"),
        _i("cilantro",            1,   "bunch",      "produce"),
        _i("cumin",               1.5, "tsp",        "spice",   True),
        _i("chili powder",        1,   "tsp",        "spice",   True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["quick", "high-protein"]),

    # ── Italian Pescatarian ────────────────────────────────────────────────────
    _r("PSC-ITA-001", "Shrimp Scampi", "italian", "shrimp", [
        _i("shrimp",              1.5, "lbs",        "protein"),
        _i("linguine",            12,  "oz",         "grain"),
        _i("lemon",               2,   "count",      "produce"),
        _i("parsley",             1,   "bunch",      "produce"),
        _i("garlic",              6,   "cloves",     "produce", True),
        _i("butter",              4,   "tbsp",       "dairy",   True),
        _i("olive oil",           3,   "tbsp",       "pantry",  True),
        _i("red pepper flakes",   0.5, "tsp",        "spice",   True),
    ], 4, 20, "weeknight", tags=["elegant", "quick"]),

    _r("PSC-ITA-002", "Salmon with Capers and Pasta", "italian", "salmon", [
        _i("salmon fillets",      1.5, "lbs",        "protein"),
        _i("pasta",               12,  "oz",         "grain"),
        _i("capers",              3,   "tbsp",       "pantry",  True),
        _i("cherry tomatoes",     1,   "pint",       "produce"),
        _i("lemon",               1,   "count",      "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("olive oil",           3,   "tbsp",       "pantry",  True),
        _i("parsley",             1,   "bunch",      "produce"),
    ], 4, 25, "weeknight", df=True, tags=["elegant", "omega-3"]),

    # ── Asian Pescatarian ──────────────────────────────────────────────────────
    _r("PSC-ASN-001", "Teriyaki Salmon Bowls", "asian", "salmon", [
        _i("salmon fillets",      1.5, "lbs",        "protein"),
        _i("brown rice",          2,   "cups",       "grain"),
        _i("broccoli",            1,   "large head", "produce"),
        _i("edamame",             1,   "cup",        "legumes"),
        _i("green onions",        3,   "stalks",     "produce"),
        _i("soy sauce",           3,   "tbsp",       "pantry",  True),
        _i("honey",               2,   "tbsp",       "pantry",  True),
        _i("sesame oil",          1,   "tbsp",       "pantry",  True),
        _i("ginger",              1,   "tsp",        "spice",   True),
    ], 4, 25, "weeknight", df=True, tags=["omega-3", "meal-prep"]),

    _r("PSC-ASN-002", "Shrimp Pad Thai", "asian", "shrimp", [
        _i("shrimp",              1.5, "lbs",        "protein"),
        _i("rice noodles",        8,   "oz",         "grain"),
        _i("bean sprouts",        2,   "cups",       "produce"),
        _i("green onions",        4,   "stalks",     "produce"),
        _i("eggs",                2,   "large",      "protein"),
        _i("peanuts",             0.25,"cup",        "pantry",  True),
        _i("fish sauce",          2,   "tbsp",       "pantry",  True),
        _i("lime",                2,   "count",      "produce"),
        _i("sesame oil",          1,   "tbsp",       "pantry",  True),
    ], 4, 30, "weeknight", gf=True, df=True, tags=["Thai", "takeout-at-home"]),

    _r("PSC-ASN-003", "Miso-Glazed Cod with Bok Choy", "asian", "cod", [
        _i("cod fillets",         1.5, "lbs",        "protein"),
        _i("bok choy",            2,   "heads",      "produce"),
        _i("brown rice",          2,   "cups",       "grain"),
        _i("miso paste",          3,   "tbsp",       "pantry",  True),
        _i("soy sauce",           2,   "tbsp",       "pantry",  True),
        _i("honey",               1,   "tbsp",       "pantry",  True),
        _i("sesame oil",          1,   "tbsp",       "pantry",  True),
        _i("ginger",              1,   "tsp",        "spice",   True),
    ], 4, 25, "weeknight", gf=True, df=True, tags=["light", "Japanese-inspired"]),

    # ── American Pescatarian ───────────────────────────────────────────────────
    _r("PSC-AMR-001", "Salmon Patties with Roasted Veg", "american_comfort", "salmon", [
        _i("canned salmon",       2,   "14.75oz cans","protein"),
        _i("breadcrumbs",         0.5, "cup",         "pantry",  True),
        _i("eggs",                2,   "large",       "protein"),
        _i("broccoli",            1,   "large head",  "produce"),
        _i("sweet potato",        2,   "medium",      "produce"),
        _i("lemon",               1,   "count",       "produce"),
        _i("olive oil",           3,   "tbsp",        "pantry",  True),
        _i("garlic powder",       0.5, "tsp",         "spice",   True),
    ], 4, 35, "weeknight", df=True, tags=["budget-friendly", "omega-3"]),

    _r("PSC-AMR-002", "Shrimp and Grits", "american_comfort", "shrimp", [
        _i("shrimp",              1.5, "lbs",        "protein"),
        _i("stone-ground grits",  1,   "cup",        "grain"),
        _i("cheddar cheese",      1,   "cup",        "dairy"),
        _i("cherry tomatoes",     1,   "pint",       "produce"),
        _i("green onions",        4,   "stalks",     "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("butter",              2,   "tbsp",       "dairy",   True),
        _i("Cajun seasoning",     1,   "tsp",        "spice",   True),
    ], 4, 30, "weeknight", gf=True, tags=["Southern", "comfort"]),

    # ── Mediterranean Pescatarian ──────────────────────────────────────────────
    _r("PSC-MED-001", "Mediterranean Baked Salmon", "mediterranean", "salmon", [
        _i("salmon fillets",      1.5, "lbs",        "protein"),
        _i("cherry tomatoes",     1,   "pint",       "produce"),
        _i("kalamata olives",     0.5, "cup",        "pantry",  True),
        _i("lemon",               2,   "count",      "produce"),
        _i("garlic",              4,   "cloves",     "produce", True),
        _i("fresh dill",          1,   "bunch",      "produce"),
        _i("olive oil",           3,   "tbsp",       "pantry",  True),
        _i("oregano",             1,   "tsp",        "spice",   True),
        _i("quinoa",              1.5, "cups",       "grain"),
    ], 4, 30, "weeknight", gf=True, df=True, tags=["omega-3", "fresh"]),

    _r("PSC-MED-002", "Shrimp Saganaki with Orzo", "mediterranean", "shrimp", [
        _i("shrimp",              1.5, "lbs",        "protein"),
        _i("orzo",                12,  "oz",         "grain"),
        _i("feta cheese",         4,   "oz",         "dairy"),
        _i("canned diced tomatoes",1,  "14oz can",   "canned"),
        _i("bell pepper",         1,   "count",      "produce"),
        _i("yellow onion",        1,   "medium",     "produce"),
        _i("garlic",              3,   "cloves",     "produce", True),
        _i("olive oil",           2,   "tbsp",       "pantry",  True),
        _i("oregano",             1,   "tsp",        "spice",   True),
    ], 4, 30, "weeknight", tags=["Greek-inspired", "elegant"]),
]


# ── Master recipe list — all cuisines + all dietary identities ────────────────
# Order: original 150 first (stable IDs), then new dietary-identity collections.
# Phase 3: replace with DB-backed recipe store once at 50+ households.
ALL_RECIPES: list[dict] = (
    MEXICAN + ITALIAN + ASIAN + AMERICAN + MEDITERRANEAN
    + VEGAN + VEGETARIAN + PESCATARIAN
)

# Populate the ID lookup now that ALL_RECIPES is fully assembled.
# get_recipe() and query_recipes() use _BY_ID at call time, not import time.
_BY_ID.update({r["id"]: r for r in ALL_RECIPES})

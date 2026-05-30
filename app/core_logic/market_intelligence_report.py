"""
market_intelligence_report.py -- WhollyFare® Market Intelligence PDF Report Generator

Generates a professional, investor-quality weekly price intelligence report.
Shows which grocery chain wins each ingredient category, with avg sale price
per chain, item counts, and a narrative summary.

No household data. No individual purchase records. Pure category-level price signal.
This is the Sincere Strategy in document form: honest, verifiable, unsponsored.

Usage:
    from app.core_logic.market_intelligence_report import build_report
    pdf_bytes = build_report(rows, metro_label="Charlottesville, VA", week="2026-05-26")
    st.download_button("Download report", pdf_bytes, "whollyfare_market_intelligence.pdf")
"""

from __future__ import annotations
import io
from collections import defaultdict
from datetime import date

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.platypus import KeepTogether

# ── Brand colours ─────────────────────────────────────────────────────────────
_GREEN_DARK   = colors.HexColor("#0F1F14")
_GREEN_MED    = colors.HexColor("#1E5C32")
_GREEN_LIGHT  = colors.HexColor("#5DAA6A")
_GREEN_PALE   = colors.HexColor("#D4EDDA")
_ORANGE       = colors.HexColor("#F28B30")
_ORANGE_PALE  = colors.HexColor("#FFF8EE")
_GREY_RULE    = colors.HexColor("#E0E0E0")
_WHITE        = colors.white
_OFF_WHITE    = colors.HexColor("#F7FBF8")
_TEXT_DARK    = colors.HexColor("#1A2E1D")
_TEXT_MID     = colors.HexColor("#5A7A62")
_TEXT_LIGHT   = colors.HexColor("#9AA8A0")

# ── Category labels ───────────────────────────────────────────────────────────
CATEGORY_LABELS = {
    "protein":   "Protein",
    "produce":   "Produce",
    "dairy":     "Dairy & Eggs",
    "pantry":    "Pantry",
    "seafood":   "Seafood",
    "bakery":    "Bakery",
    "frozen":    "Frozen",
    "snacks":    "Snacks",
    "beverages": "Beverages",
    "other":     "Other",
}
CATEGORY_ORDER = ["protein", "produce", "dairy", "pantry", "seafood",
                   "bakery", "frozen", "snacks", "beverages", "other"]


def _process_rows(rows: list[dict]) -> tuple[dict, list[str], dict]:
    """
    Aggregate raw flyer item rows into:
      - cat_chain: dict[category][chain] -> list of prices
      - chains_list: sorted list of chain names present
      - winners: dict[category] -> winning chain name
    """
    cat_chain: dict = defaultdict(lambda: defaultdict(list))
    chains_seen: set = set()

    for r in rows:
        chain    = r.get("chain") or "Unknown"
        category = r.get("category") or "other"
        price    = r.get("sale_price_per_unit")
        if price and float(price) > 0:
            cat_chain[category][chain].append(float(price))
            chains_seen.add(chain)

    chains_list = sorted(chains_seen)

    # Compute average price per category per chain
    avgs: dict = {}
    for cat, chain_data in cat_chain.items():
        avgs[cat] = {ch: round(sum(v) / len(v), 2) for ch, v in chain_data.items() if v}

    winners: dict = {}
    for cat, chain_avgs in avgs.items():
        if chain_avgs:
            winners[cat] = min(chain_avgs, key=chain_avgs.get)

    return cat_chain, avgs, chains_list, winners


def _build_narrative(winners: dict, avgs: dict) -> str:
    """Generate a plain-English summary paragraph from the winner data."""
    from collections import Counter
    win_counts = Counter(winners.values())
    if not win_counts:
        return "Insufficient data to generate summary."

    top = win_counts.most_common(1)[0]
    top_chain, top_n = top
    top_cats = [CATEGORY_LABELS.get(c, c) for c, w in winners.items() if w == top_chain]

    lines = []
    lines.append(
        f"{top_chain} led this week with the lowest average sale prices in "
        f"{top_n} categor{'y' if top_n == 1 else 'ies'}: {', '.join(top_cats)}."
    )

    others = [(ch, cnt) for ch, cnt in win_counts.most_common() if ch != top_chain]
    for ch, cnt in others[:3]:
        cats = [CATEGORY_LABELS.get(c, c) for c, w in winners.items() if w == ch]
        lines.append(f"{ch} led {', '.join(cats)}.")

    lines.append(
        "All prices are average sale prices per unit across items loaded for the week. "
        "Lower average indicates stronger promotional pricing in that category."
    )
    return " ".join(lines)


def build_report(
    rows: list[dict],
    metro_label: str = "Charlottesville, VA",
    week: str | None = None,
) -> bytes:
    """
    Build a Market Intelligence PDF report from raw platform_flyer_items rows.

    Parameters
    ----------
    rows        : list of dicts with keys chain, category, sale_price_per_unit, name
    metro_label : human-readable market label shown on the report
    week        : ISO week start date string (e.g. "2026-05-26")

    Returns
    -------
    bytes : raw PDF content, ready for st.download_button
    """
    week = week or date.today().isoformat()
    cat_chain, avgs, chains_list, winners = _process_rows(rows)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"WhollyFare Market Intelligence — {metro_label} — {week}",
        author="WhollyFare®",
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Cover header ─────────────────────────────────────────────────────────
    def _p(text, style):
        return Paragraph(text, style)

    eyebrow_style = ParagraphStyle(
        "Eyebrow",
        fontName="Helvetica",
        fontSize=7,
        textColor=_GREEN_LIGHT,
        spaceAfter=4,
        letterSpacing=1.5,
    )
    title_style = ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=_GREEN_DARK,
        spaceAfter=6,
        leading=26,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName="Helvetica",
        fontSize=11,
        textColor=_TEXT_MID,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=9,
        textColor=_TEXT_DARK,
        spaceAfter=6,
        leading=14,
    )
    caption_style = ParagraphStyle(
        "Caption",
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        textColor=_TEXT_LIGHT,
        spaceAfter=4,
        leading=11,
    )
    section_label_style = ParagraphStyle(
        "SectionLabel",
        fontName="Helvetica-Bold",
        fontSize=7,
        textColor=_GREEN_MED,
        spaceAfter=3,
        letterSpacing=1.2,
    )
    winner_summary_style = ParagraphStyle(
        "WinnerSummary",
        fontName="Helvetica",
        fontSize=9,
        textColor=_TEXT_DARK,
        spaceAfter=4,
        leading=14,
        backColor=_OFF_WHITE,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=6,
    )

    story.append(_p("WHOLLYFARE® MARKET INTELLIGENCE", eyebrow_style))
    story.append(_p(f"Weekly Price Index · {metro_label}", title_style))
    story.append(_p(f"Week of {week}  ·  {len(rows):,} sale items analyzed  ·  {len(chains_list)} grocery chains", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=_GREEN_MED, spaceAfter=12))

    # ── Disclosure ────────────────────────────────────────────────────────────
    story.append(_p(
        "This report contains no household data, no individual purchase records, and no personally "
        "identifiable information. All figures are aggregate average sale prices per unit, derived "
        "from weekly grocery circulars loaded to the WhollyFare® platform. No grocer paid for "
        "placement. No algorithm was tuned to favor any chain. This is pure price signal.",
        caption_style,
    ))
    story.append(Spacer(1, 10))

    # ── Category winner table ─────────────────────────────────────────────────
    story.append(_p("CATEGORY PRICE LEADERS", section_label_style))
    story.append(_p(
        "Average sale price per unit by ingredient category. The winning chain (lowest average) "
        "is highlighted. Item count in parentheses.",
        caption_style,
    ))
    story.append(Spacer(1, 6))

    # Build table data
    # Header row
    col_widths = [1.5 * inch] + [1.1 * inch] * len(chains_list) + [1.2 * inch]
    header_row = ["Category"] + chains_list + ["Winner"]
    table_data = [header_row]

    present_cats = [c for c in CATEGORY_ORDER if c in avgs and avgs[c]]

    for cat in present_cats:
        cat_avgs = avgs[cat]
        cat_data = cat_chain[cat]
        winner   = winners.get(cat, "")
        label    = CATEGORY_LABELS.get(cat, cat)

        row = [label]
        for ch in chains_list:
            if ch in cat_avgs:
                cnt  = len(cat_data.get(ch, []))
                cell = f"${cat_avgs[ch]:.2f} ({cnt} items)"
            else:
                cell = "—"
            row.append(cell)
        row.append(winner)
        table_data.append(row)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Base table style
    ts = TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), _GREEN_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _GREEN_LIGHT),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 7),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("ALIGN",         (0, 0), (0, 0),  "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        # Body
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("ALIGN",         (1, 1), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 1), (0, -1),  "LEFT"),
        ("TEXTCOLOR",     (0, 1), (-1, -1), _TEXT_DARK),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_WHITE, _OFF_WHITE]),
        ("GRID",          (0, 0), (-1, -1), 0.5, _GREY_RULE),
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        # Category label column bold
        ("FONTNAME",      (0, 1), (0, -1),  "Helvetica-Bold"),
        # Winner column
        ("BACKGROUND",    (-1, 0), (-1, 0), _GREEN_DARK),
        ("TEXTCOLOR",     (-1, 1), (-1, -1), _WHITE),
        ("BACKGROUND",    (-1, 1), (-1, -1), _ORANGE),
        ("FONTNAME",      (-1, 1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (-1, 1), (-1, -1), 7.5),
    ])

    # Highlight winner cell in each row
    for row_idx, cat in enumerate(present_cats, start=1):
        winner_chain = winners.get(cat)
        if winner_chain and winner_chain in chains_list:
            col_idx = chains_list.index(winner_chain) + 1  # +1 for category label col
            ts.add("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), _GREEN_PALE)
            ts.add("TEXTCOLOR",  (col_idx, row_idx), (col_idx, row_idx), _GREEN_MED)
            ts.add("FONTNAME",   (col_idx, row_idx), (col_idx, row_idx), "Helvetica-Bold")

    tbl.setStyle(ts)
    story.append(tbl)
    story.append(Spacer(1, 16))

    # ── Winner summary ────────────────────────────────────────────────────────
    story.append(_p("THIS WEEK'S SUMMARY", section_label_style))
    from collections import Counter
    win_counts = Counter(winners.values())
    summary_lines = []
    for chain, cnt in win_counts.most_common():
        cats_won = [CATEGORY_LABELS.get(c, c) for c, w in winners.items() if w == chain]
        summary_lines.append(
            f"<b>{chain}</b>: {cnt} categor{'y' if cnt == 1 else 'ies'} — {', '.join(cats_won)}"
        )
    story.append(_p("<br/>".join(summary_lines), winner_summary_style))
    story.append(Spacer(1, 10))

    # ── Narrative paragraph ───────────────────────────────────────────────────
    story.append(_p("ANALYSIS", section_label_style))
    story.append(_p(_build_narrative(winners, avgs), body_style))
    story.append(Spacer(1, 16))

    # ── Footer rule + disclosure ──────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=_GREY_RULE, spaceAfter=8))
    story.append(_p(
        "WhollyFare® · Sentir Solutions® LLC · Charlottesville, VA · whollyfare.com  |  "
        "The Sincere Strategy®: Zero paid placements. Honest math. Household first. Always.  |  "
        f"Generated {date.today().isoformat()}  |  "
        "No household data. No individually identifiable information. Public price signal only.",
        caption_style,
    ))

    doc.build(story)
    return buf.getvalue()

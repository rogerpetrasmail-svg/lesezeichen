"""Reine (Qt-unabhängige) Logik zur Aufbereitung der Modell-Antwort.

Bewusst frei von GUI-/Qt-Importen, damit sie isoliert testbar ist.
"""

from __future__ import annotations

from .rss import FeedItem


def normalize_result(raw: dict, item: FeedItem) -> dict:
    """Bringt das Modell-JSON in das DB-Schema (mit Plausibilitätsprüfung)."""
    try:
        score = int(round(float(raw.get("relevanz_score", 0))))
    except (TypeError, ValueError):
        score = 0
    score = max(1, min(10, score)) if score else 0

    kategorien = raw.get("kategorien", [])
    if isinstance(kategorien, str):
        kategorien = [kategorien]
    kategorie = ", ".join(str(k).strip() for k in kategorien if str(k).strip())

    titel = str(raw.get("titel") or item.title).strip()

    return {
        "guid": item.guid,
        "titel": titel,
        "kategorie": kategorie,
        "score": score,
        "schwerpunkt": str(raw.get("schwerpunkt", "")).strip(),
        "zusammenfassung": str(raw.get("zusammenfassung", "")).strip(),
        "original_beitrag": item.content,
        "quelle_url": item.source_url,
        "link": item.link,
    }

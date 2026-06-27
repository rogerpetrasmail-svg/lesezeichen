"""RSS-/Atom-Feed-Auslesung über feedparser.

Extrahiert Titel und (bestmöglich) den Volltext/Inhalt jedes Beitrags und
liefert eine stabile GUID zur Duplikaterkennung.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

import feedparser


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(raw: str) -> str:
    """Entfernt HTML-Tags und normalisiert Whitespace."""
    if not raw:
        return ""
    text = _TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class FeedItem:
    guid: str
    title: str
    content: str
    link: str
    source_url: str
    raw_content: str = field(default="")


def _best_content(entry) -> str:
    """Findet den ausführlichsten verfügbaren Inhalt eines Eintrags."""
    # feedparser bietet je nach Feed unterschiedliche Felder
    if entry.get("content"):
        # Liste von content-Objekten – nimm das längste
        candidates = [c.get("value", "") for c in entry["content"]]
        longest = max(candidates, key=len) if candidates else ""
        if longest:
            return longest
    for key in ("summary_detail", "summary", "description"):
        val = entry.get(key)
        if isinstance(val, dict):
            val = val.get("value", "")
        if val:
            return val
    return entry.get("title", "")


def fetch_feed(url: str, max_items: int = 25) -> list[FeedItem]:
    """Lädt einen Feed und liefert die Beiträge als FeedItem-Liste.

    Wirft keine Ausnahme bei Netzwerkfehlern – feedparser kapselt diese; der
    Aufrufer kann ``bozo`` über ein leeres Ergebnis erkennen.
    """
    parsed = feedparser.parse(url)
    items: list[FeedItem] = []
    for entry in parsed.entries[:max_items]:
        raw = _best_content(entry)
        title = _strip_html(entry.get("title", "")) or "(ohne Titel)"
        content = _strip_html(raw)
        link = entry.get("link", "") or ""
        guid = entry.get("id") or link or f"{url}::{title}"
        items.append(
            FeedItem(
                guid=guid,
                title=title,
                content=content,
                link=link,
                source_url=url,
                raw_content=raw,
            )
        )
    return items


def feed_title(url: str) -> str:
    """Versucht, den Anzeigetitel eines Feeds zu ermitteln."""
    try:
        parsed = feedparser.parse(url)
        return _strip_html(parsed.feed.get("title", "")) or url
    except Exception:  # noqa: BLE001 - Titelermittlung darf nie blockieren
        return url

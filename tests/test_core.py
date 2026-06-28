"""Smoke-Tests für die KI-unabhängige Kernlogik (ohne GUI, ohne Ollama).

Ausführen:
    python -m pytest tests/  -q
oder ohne pytest:
    python tests/test_core.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Projekt-Wurzelverzeichnis in den Suchpfad aufnehmen, damit das Paket ``app``
# auch beim direkten Aufruf ``python tests/test_core.py`` gefunden wird.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.analysis import normalize_result
from app.database import Database
from app.excel_export import COLUMNS, export_to_excel
from app.ollama_client import OllamaClient
from app.rss import FeedItem


def test_database_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "test.sqlite3")
        # Defaults vorhanden
        assert db.get_setting("ollama_model") == "qwen2.5-coder:32b"
        assert db.list_categories()  # vorbefüllt

        db.add_feed("https://example.com/feed.xml", "Beispiel")
        assert len(db.list_feeds()) == 1

        db.add_category("Testkategorie")
        assert "Testkategorie" in db.list_categories()
        db.delete_category("Testkategorie")
        assert "Testkategorie" not in db.list_categories()

        aid = db.upsert_article(
            {
                "guid": "g1",
                "titel": "Hallo",
                "kategorie": "Technologie",
                "score": 7,
                "schwerpunkt": "Test",
                "zusammenfassung": "Eine Zusammenfassung.",
                "original_beitrag": "Original.",
            }
        )
        assert db.article_exists("g1")
        db.update_article_fields(aid, eigenes_script="Mein Script")
        assert db.get_article(aid)["eigenes_script"] == "Mein Script"

        # upsert mit gleicher guid darf keinen zweiten Datensatz erzeugen
        db.upsert_article({"guid": "g1", "titel": "Neu", "score": 9})
        assert len(db.list_articles()) == 1
        db.close()
    print("test_database_roundtrip OK")


def test_excel_export_and_recovery() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "neuer_ordner" / "File.xlsx"
        rows = [
            {
                "titel": "T1", "kategorie": "K", "score": 5,
                "schwerpunkt": "S", "zusammenfassung": "Z",
                "eigenes_script": "E", "original_beitrag": "O",
            }
        ]
        result = export_to_excel(target, rows)
        assert result.path.exists()
        assert not result.recovered  # Ordner wird automatisch erstellt
        assert [c[0] for c in COLUMNS] == [
            "Titel", "Kategorie", "Score", "Schwerpunkt",
            "Zusammenfassung", "Eigenes_Script", "Original_Beitrag",
        ]
    print("test_excel_export_and_recovery OK")


def test_normalize_result_clamps_score() -> None:
    item = FeedItem("g", "Titel", "Inhalt", "http://x", "http://feed")
    out = normalize_result(
        {"relevanz_score": 99, "kategorien": "Technologie", "schwerpunkt": "x",
         "zusammenfassung": "y"},
        item,
    )
    assert out["score"] == 10
    assert out["kategorie"] == "Technologie"
    out2 = normalize_result({"relevanz_score": -3, "kategorien": ["A", "B"]}, item)
    assert out2["score"] == 1
    assert out2["kategorie"] == "A, B"
    print("test_normalize_result_clamps_score OK")


def test_ollama_json_parsing() -> None:
    parsed = OllamaClient._parse_json('Text vorne {"a": 1, "b": "x"} Text hinten')
    assert parsed == {"a": 1, "b": "x"}
    parsed2 = OllamaClient._parse_json('{"score": 3}')
    assert parsed2["score"] == 3
    print("test_ollama_json_parsing OK")


if __name__ == "__main__":
    test_database_roundtrip()
    test_excel_export_and_recovery()
    test_normalize_result_clamps_score()
    test_ollama_json_parsing()
    print("\nAlle Tests bestanden ✅")

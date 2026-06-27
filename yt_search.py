#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yt_search.py
============

Robustes, eigenständiges Skript, um YouTube nach den neuesten Videos zu einem
oder mehreren Suchbegriffen zu durchsuchen. Das Ergebnis wird als sauberes JSON
auf stdout ausgegeben, sodass es z.B. von n8n direkt weiterverarbeitet werden
kann.

Es werden – je nach Verfügbarkeit – zwei Backends unterstützt:

1. ``api``   – Offizielle YouTube Data API v3 (Paket ``google-api-python-client``).
               Wird automatisch verwendet, wenn ein API-Key vorhanden ist
               (Argument ``--api-key`` oder Umgebungsvariable ``YOUTUBE_API_KEY``).
2. ``scrape`` – Scraping ohne API-Key über ``yt-dlp`` (bevorzugt, da stabil und
               liefert Beschreibungen) bzw. als Fallback über ``scrapetube``.

Standardmäßig wählt das Skript automatisch das beste verfügbare Backend
(API, falls Key vorhanden, sonst Scraping).

Beispiele
---------
    python yt_search.py "n8n automation"
    python yt_search.py "lokale LLMs" "ollama setup" --max 5
    python yt_search.py "python tutorial" --backend scrape --max 10
    python yt_search.py "ki news" --api-key DEIN_KEY --max 20

Abhängigkeiten (alle optional – das Skript funktioniert mit dem, was da ist):
    pip install yt-dlp
    pip install scrapetube
    pip install google-api-python-client

Exit-Codes:
    0  Erfolg (auch wenn keine Videos gefunden wurden)
    1  Laufzeit-/Konfigurationsfehler (Details im JSON unter "error")
    2  Falsche Aufrufargumente
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
def _eprint(*args, **kwargs):
    """Diagnose-Ausgaben gehen nach stderr, damit stdout reines JSON bleibt."""
    print(*args, file=sys.stderr, **kwargs)


def _print_json(payload):
    """Gibt das Ergebnis als formatiertes, UTF-8-sicheres JSON auf stdout aus."""
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.stdout.flush()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _safe_iso_from_timestamp(ts):
    """Wandelt einen Unix-Timestamp in einen ISO-8601-String (UTC) um."""
    if ts in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError, TypeError):
        return None


def _iso_from_yyyymmdd(value):
    """yt-dlp liefert ``upload_date`` häufig als 'YYYYMMDD'."""
    if not value:
        return None
    value = str(value)
    if len(value) == 8 and value.isdigit():
        try:
            return datetime.strptime(value, "%Y%m%d").replace(
                tzinfo=timezone.utc
            ).isoformat()
        except ValueError:
            return None
    return value


def _truncate(text, limit):
    if text is None:
        return None
    text = str(text).strip()
    if limit and limit > 0 and len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


def _normalize_video(*, video_id, title, channel, published, url, description):
    return {
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "published": published,
        "url": url or (f"https://www.youtube.com/watch?v={video_id}" if video_id else None),
        "description": description,
    }


# --------------------------------------------------------------------------- #
# Backend: Offizielle YouTube Data API v3
# --------------------------------------------------------------------------- #
def search_via_api(query, max_results, api_key, description_limit):
    """
    Sucht über die offizielle YouTube Data API v3.

    Wirft ``RuntimeError`` mit verständlicher Meldung, falls etwas schiefgeht.
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        raise RuntimeError(
            "Backend 'api' benötigt das Paket 'google-api-python-client'. "
            "Installiere es mit: pip install google-api-python-client"
        ) from exc

    try:
        youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)

        # Schritt 1: Suche (nach Datum sortiert -> neueste zuerst)
        search_resp = (
            youtube.search()
            .list(
                q=query,
                part="snippet",
                type="video",
                order="date",
                maxResults=min(max_results, 50),
            )
            .execute()
        )

        items = search_resp.get("items", [])
        video_ids = [
            it["id"]["videoId"]
            for it in items
            if it.get("id", {}).get("videoId")
        ]

        # Schritt 2: Volle Beschreibungen nachladen (search liefert nur gekürzt)
        descriptions = {}
        if video_ids:
            details = (
                youtube.videos()
                .list(part="snippet", id=",".join(video_ids))
                .execute()
            )
            for d in details.get("items", []):
                snip = d.get("snippet", {})
                descriptions[d["id"]] = snip.get("description")

        results = []
        for it in items:
            vid = it.get("id", {}).get("videoId")
            snip = it.get("snippet", {})
            results.append(
                _normalize_video(
                    video_id=vid,
                    title=snip.get("title"),
                    channel=snip.get("channelTitle"),
                    published=snip.get("publishedAt"),
                    url=f"https://www.youtube.com/watch?v={vid}" if vid else None,
                    description=_truncate(
                        descriptions.get(vid, snip.get("description")),
                        description_limit,
                    ),
                )
            )
        return results

    except HttpError as exc:
        status = getattr(exc, "status_code", None) or getattr(
            getattr(exc, "resp", None), "status", None
        )
        raise RuntimeError(
            f"YouTube API Fehler (HTTP {status}): {exc}. "
            "Pruefe API-Key, Kontingent (Quota) und ob die 'YouTube Data API v3' "
            "im Google-Cloud-Projekt aktiviert ist."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - bewusst breit fuer robustes Verhalten
        raise RuntimeError(f"Unerwarteter Fehler bei der API-Suche: {exc}") from exc


# --------------------------------------------------------------------------- #
# Backend: Scraping über yt-dlp
# --------------------------------------------------------------------------- #
def search_via_ytdlp(query, max_results, description_limit, fetch_descriptions):
    """
    Sucht über yt-dlp (kein API-Key noetig).

    yt-dlp unterstuetzt die Pseudo-URL ``ytsearchdate<N>:<query>`` -> neueste
    Videos zuerst. Wirft ``RuntimeError`` bei fehlendem Paket / Fehlern.
    """
    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError as exc:
        raise RuntimeError(
            "Backend 'scrape' (yt-dlp) benötigt das Paket 'yt-dlp'. "
            "Installiere es mit: pip install yt-dlp"
        ) from exc

    # "ytsearchdate" sortiert nach Datum (neueste zuerst).
    search_url = f"ytsearchdate{int(max_results)}:{query}"

    # extract_flat = True ist schnell, liefert aber keine Beschreibungen.
    # Fuer Beschreibungen muessen wir je Video die volle Info ziehen.
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist" if not fetch_descriptions else False,
        "ignoreerrors": True,
        "socket_timeout": 20,
        "noprogress": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
    except DownloadError as exc:
        raise RuntimeError(
            f"yt-dlp konnte die Suche nicht ausfuehren: {exc}. "
            "Moeglicherweise blockt YouTube gerade oder es besteht keine "
            "Internetverbindung."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unerwarteter Fehler bei yt-dlp: {exc}") from exc

    if not info:
        return []

    entries = info.get("entries") or []
    results = []
    for entry in entries:
        if not entry:
            continue

        vid = entry.get("id")

        # Veroeffentlichungsdatum: je nach Modus unterschiedlich vorhanden
        published = (
            _iso_from_yyyymmdd(entry.get("upload_date"))
            or _safe_iso_from_timestamp(entry.get("timestamp"))
            or entry.get("release_timestamp")
            and _safe_iso_from_timestamp(entry.get("release_timestamp"))
            or None
        )

        results.append(
            _normalize_video(
                video_id=vid,
                title=entry.get("title"),
                channel=entry.get("channel") or entry.get("uploader"),
                published=published,
                url=entry.get("webpage_url")
                or entry.get("url")
                or (f"https://www.youtube.com/watch?v={vid}" if vid else None),
                description=_truncate(entry.get("description"), description_limit),
            )
        )

    return results


# --------------------------------------------------------------------------- #
# Backend: Scraping über scrapetube (Fallback)
# --------------------------------------------------------------------------- #
def search_via_scrapetube(query, max_results, description_limit):
    """
    Fallback-Scraper über 'scrapetube'. Liefert leider keine vollen
    Beschreibungen und ungenaue Datumsangaben (z.B. 'vor 2 Tagen').
    """
    try:
        import scrapetube
    except ImportError as exc:
        raise RuntimeError(
            "Fallback-Backend benötigt das Paket 'scrapetube'. "
            "Installiere es mit: pip install scrapetube"
        ) from exc

    try:
        videos = scrapetube.get_search(query, limit=max_results, sort_by="upload_date")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"scrapetube-Suche fehlgeschlagen: {exc}. "
            "Moeglicherweise blockt YouTube oder das Netz ist weg."
        ) from exc

    results = []
    try:
        for v in videos:
            vid = v.get("videoId")
            title_runs = (v.get("title") or {}).get("runs") or []
            title = "".join(r.get("text", "") for r in title_runs) or None

            channel = None
            owner = (
                v.get("ownerText", {}).get("runs")
                or v.get("longBylineText", {}).get("runs")
                or []
            )
            if owner:
                channel = "".join(r.get("text", "") for r in owner) or None

            # Relatives Datum, z.B. "vor 3 Tagen"
            published = None
            pub = v.get("publishedTimeText", {})
            if isinstance(pub, dict):
                published = pub.get("simpleText")

            desc = None
            snippets = v.get("detailedMetadataSnippets") or []
            if snippets:
                snip_runs = (
                    snippets[0].get("snippetText", {}).get("runs") or []
                )
                desc = "".join(r.get("text", "") for r in snip_runs) or None

            results.append(
                _normalize_video(
                    video_id=vid,
                    title=title,
                    channel=channel,
                    published=published,
                    url=f"https://www.youtube.com/watch?v={vid}" if vid else None,
                    description=_truncate(desc, description_limit),
                )
            )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Fehler beim Auswerten der scrapetube-Daten: {exc}") from exc

    return results


# --------------------------------------------------------------------------- #
# Backend-Auswahl & Orchestrierung
# --------------------------------------------------------------------------- #
def run_search(query, max_results, backend, api_key, description_limit,
               fetch_descriptions):
    """
    Fuehrt die Suche fuer einen einzelnen Suchbegriff aus und gibt
    (videos, used_backend) zurueck. Wirft RuntimeError bei harten Fehlern.
    """
    if backend == "api":
        return search_via_api(query, max_results, api_key, description_limit), "api"

    if backend == "scrape":
        # Erst yt-dlp, bei fehlendem Paket Fallback auf scrapetube.
        try:
            return (
                search_via_ytdlp(
                    query, max_results, description_limit, fetch_descriptions
                ),
                "yt-dlp",
            )
        except RuntimeError as exc:
            _eprint(f"[warn] yt-dlp nicht nutzbar ({exc}). Versuche scrapetube...")
            return (
                search_via_scrapetube(query, max_results, description_limit),
                "scrapetube",
            )

    # backend == "auto"
    if api_key:
        try:
            return search_via_api(query, max_results, api_key, description_limit), "api"
        except RuntimeError as exc:
            _eprint(f"[warn] API-Backend fehlgeschlagen ({exc}). Wechsle zu Scraping...")

    # Kein Key oder API fehlgeschlagen -> Scraping
    try:
        return (
            search_via_ytdlp(
                query, max_results, description_limit, fetch_descriptions
            ),
            "yt-dlp",
        )
    except RuntimeError as exc:
        _eprint(f"[warn] yt-dlp nicht nutzbar ({exc}). Versuche scrapetube...")
        return (
            search_via_scrapetube(query, max_results, description_limit),
            "scrapetube",
        )


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Durchsucht YouTube nach den neuesten Videos zu einem Thema "
        "und gibt das Ergebnis als JSON aus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "queries",
        nargs="+",
        help="Ein oder mehrere Suchbegriffe/Themen (in Anfuehrungszeichen).",
    )
    parser.add_argument(
        "--max",
        "-n",
        type=int,
        default=10,
        dest="max_results",
        help="Maximale Anzahl Videos pro Suchbegriff (Standard: 10).",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "api", "scrape"],
        default="auto",
        help="Welches Backend genutzt wird (Standard: auto).",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("YOUTUBE_API_KEY"),
        help="YouTube Data API v3 Key (oder Umgebungsvariable YOUTUBE_API_KEY).",
    )
    parser.add_argument(
        "--description-limit",
        type=int,
        default=500,
        help="Beschreibung auf N Zeichen kuerzen (0 = nicht kuerzen, Standard: 500).",
    )
    parser.add_argument(
        "--no-descriptions",
        action="store_true",
        help="Beschreibungen NICHT laden (beim Scraping deutlich schneller).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.max_results < 1:
        _eprint("[error] --max muss >= 1 sein.")
        return 2

    fetch_descriptions = not args.no_descriptions

    result = {
        "generated_at": _now_iso(),
        "backend_requested": args.backend,
        "query_count": len(args.queries),
        "results": [],
    }

    had_hard_error = False

    for query in args.queries:
        block = {
            "query": query,
            "backend_used": None,
            "count": 0,
            "videos": [],
            "error": None,
        }
        try:
            videos, used_backend = run_search(
                query=query,
                max_results=args.max_results,
                backend=args.backend,
                api_key=args.api_key,
                description_limit=args.description_limit,
                fetch_descriptions=fetch_descriptions,
            )
            block["backend_used"] = used_backend
            block["videos"] = videos
            block["count"] = len(videos)
        except RuntimeError as exc:
            block["error"] = str(exc)
            had_hard_error = True
            _eprint(f"[error] Suche fuer '{query}' fehlgeschlagen: {exc}")
        except KeyboardInterrupt:
            _eprint("[abort] Vom Benutzer abgebrochen.")
            return 1
        except Exception as exc:  # noqa: BLE001 - letzter Sicherheitsnetz-Fallback
            block["error"] = f"Unerwarteter Fehler: {exc}"
            had_hard_error = True
            _eprint(f"[error] Unerwarteter Fehler bei '{query}': {exc}")

        result["results"].append(block)

    _print_json(result)

    # Exit-Code 1 nur, wenn ALLE Suchanfragen fehlschlugen (sonst Teil-Erfolg = 0)
    all_failed = had_hard_error and all(
        b["error"] is not None for b in result["results"]
    )
    return 1 if all_failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _eprint("[abort] Vom Benutzer abgebrochen.")
        sys.exit(1)

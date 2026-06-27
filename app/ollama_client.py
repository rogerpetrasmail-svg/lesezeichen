"""HTTP-Client für die lokale Ollama-Instanz.

Nutzt ausschliesslich den lokalen Endpunkt (Standard http://localhost:11434).
Es werden KEINE externen Cloud-Dienste kontaktiert.
"""

from __future__ import annotations

import json
from typing import Any

import requests

from . import config


class OllamaError(RuntimeError):
    """Fehler bei der Kommunikation mit Ollama."""


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or config.DEFAULT_OLLAMA_URL).rstrip("/")
        self.model = model or config.DEFAULT_OLLAMA_MODEL

    # ------------------------------------------------------------------ checks
    def is_available(self, timeout: float = 3.0) -> bool:
        """Prüft, ob der Ollama-Server erreichbar ist."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self, timeout: float = 5.0) -> list[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except requests.RequestException as exc:
            raise OllamaError(f"Modelle konnten nicht geladen werden: {exc}") from exc

    # ---------------------------------------------------------------- analysis
    def analyze(
        self,
        system_prompt: str,
        user_content: str,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Sendet einen Beitrag an Ollama und erwartet sauberes JSON zurück.

        Verwendet Ollamas natives ``format: "json"`` für strukturierte Ausgabe.
        """
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat", json=payload, timeout=timeout
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(
                f"Ollama-Anfrage fehlgeschlagen ({self.base_url}): {exc}"
            ) from exc

        try:
            envelope = resp.json()
            content = envelope.get("message", {}).get("content", "")
            if not content:
                raise OllamaError("Leere Antwort von Ollama erhalten.")
            return self._parse_json(content)
        except (ValueError, KeyError) as exc:
            raise OllamaError(f"Antwort konnte nicht gelesen werden: {exc}") from exc

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        """Robustes Parsen der Modell-Antwort.

        Auch wenn ``format=json`` aktiv ist, kann ein Modell gelegentlich
        zusätzlichen Text liefern – wir extrahieren das erste JSON-Objekt.
        """
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(content[start : end + 1])
                except json.JSONDecodeError as exc:
                    raise OllamaError(
                        f"Ungültiges JSON von Ollama: {exc}"
                    ) from exc
            raise OllamaError("Antwort enthielt kein gültiges JSON-Objekt.")

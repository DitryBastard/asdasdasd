"""Glossary / termbase: exact-match terminology, kept separate from the
similarity-matched translation memory (see app/vector_store.py).

A translation-memory match is "probably relevant, reuse where it fits" -
appropriate for whole sentences, where overall meaning is what matters. A
glossary entry is "this specific term must translate to exactly this" - a
hard constraint that semantic similarity search cannot express (two term
translations can be semantically close and still be the wrong one for house
style or an established product name). Lookups here are a plain substring
check against a small, hand-curated list, not vector search, so a
lightweight JSON file is a better fit than routing this through Chroma.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import settings


def _load() -> list[dict]:
    path = Path(settings.glossary_path)
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _save(entries: list[dict]) -> None:
    path = Path(settings.glossary_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def list_entries(source_lang: str | None = None, target_lang: str | None = None) -> list[dict]:
    entries = _load()
    if source_lang:
        entries = [e for e in entries if e.get("source_lang") == source_lang]
    if target_lang:
        entries = [e for e in entries if e.get("target_lang") == target_lang]
    return sorted(entries, key=lambda e: e.get("created_at", ""), reverse=True)


def add_entry(source_term: str, target_term: str, source_lang: str, target_lang: str, note: str = "") -> dict:
    entries = _load()
    entry = {
        "id": str(uuid.uuid4()),
        "source_term": source_term.strip(),
        "target_term": target_term.strip(),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "note": note.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    _save(entries)
    return entry


def delete_entry(entry_id: str) -> None:
    _save([e for e in _load() if e.get("id") != entry_id])


def find_applicable_terms(sentence: str, entries: list[dict]) -> list[dict]:
    """Glossary entries whose source_term appears (case-insensitively) as a
    substring of the sentence about to be translated."""
    lowered = sentence.lower()
    return [entry for entry in entries if entry["source_term"] and entry["source_term"].lower() in lowered]

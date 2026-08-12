from app import glossary_store
from app.glossary_store import find_applicable_terms


def _entry(source_term: str, target_term: str = "x") -> dict:
    return {"source_term": source_term, "target_term": target_term}


def test_find_applicable_terms_matches_substring_case_insensitively():
    entries = [_entry("timeout"), _entry("control valve")]
    matches = find_applicable_terms("Set the Timeout parameter before starting.", entries)
    assert [m["source_term"] for m in matches] == ["timeout"]


def test_find_applicable_terms_returns_empty_for_no_match():
    entries = [_entry("timeout")]
    assert find_applicable_terms("This sentence has nothing relevant.", entries) == []


def test_find_applicable_terms_matches_multiple_terms():
    entries = [_entry("timeout"), _entry("control valve"), _entry("unrelated term")]
    matches = find_applicable_terms("The control valve has a timeout setting.", entries)
    assert {m["source_term"] for m in matches} == {"timeout", "control valve"}


def test_find_applicable_terms_ignores_blank_source_term():
    entries = [_entry("")]
    assert find_applicable_terms("Any sentence at all.", entries) == []


def test_add_list_delete_round_trip():
    added = glossary_store.add_entry("timeout", "тайм-аут", "en", "ru", note="always lowercase in ru")
    assert added["source_term"] == "timeout"
    assert added["target_term"] == "тайм-аут"
    assert added["id"]

    entries = glossary_store.list_entries("en", "ru")
    assert any(e["id"] == added["id"] for e in entries)

    glossary_store.delete_entry(added["id"])
    entries_after = glossary_store.list_entries("en", "ru")
    assert not any(e["id"] == added["id"] for e in entries_after)


def test_list_entries_filters_by_language_pair():
    glossary_store.add_entry("widget", "виджет", "en", "ru")
    glossary_store.add_entry("Werkzeug", "инструмент", "de", "ru")

    en_ru_terms = {e["source_term"] for e in glossary_store.list_entries("en", "ru")}
    de_ru_terms = {e["source_term"] for e in glossary_store.list_entries("de", "ru")}

    assert "widget" in en_ru_terms
    assert "widget" not in de_ru_terms
    assert "Werkzeug" in de_ru_terms

from app.config import settings
from app.translation_service import _best_match


def make_candidate(similarity: float, source: str = "src", target: str = "tgt") -> dict:
    return {
        "similarity": similarity,
        "source_text": source,
        "target_text": target,
        "document_title": "doc.docx",
    }


def test_no_candidates_returns_none():
    assert _best_match([]) is None


def test_below_fuzzy_threshold_returns_none():
    candidates = [make_candidate(settings.fuzzy_match_threshold - 0.05)]
    assert _best_match(candidates) is None


def test_fuzzy_match_classified_correctly():
    candidates = [make_candidate(settings.fuzzy_match_threshold + 0.05)]
    match = _best_match(candidates)
    assert match is not None
    assert match["type"] == "fuzzy"


def test_exact_match_classified_correctly():
    candidates = [make_candidate(settings.exact_match_threshold)]
    match = _best_match(candidates)
    assert match is not None
    assert match["type"] == "exact"


def test_picks_highest_similarity_candidate():
    candidates = [make_candidate(0.8, "a", "A"), make_candidate(0.95, "b", "B")]
    match = _best_match(candidates)
    assert match["memory_source"] == "b"
    assert match["memory_target"] == "B"


def test_match_includes_document_title():
    candidates = [make_candidate(0.99, source="Настройка сервера", target="Server configuration")]
    match = _best_match(candidates)
    assert match["document_title"] == "doc.docx"

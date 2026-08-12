from app.memory_service import preview_document_pair


def test_aligns_equal_length_paragraphs():
    source = ["Первый абзац.", "Второй абзац."]
    target = ["First paragraph.", "Second paragraph."]
    result = preview_document_pair(source, target)
    assert result["pairs"] == [
        {"source_text": "Первый абзац.", "target_text": "First paragraph."},
        {"source_text": "Второй абзац.", "target_text": "Second paragraph."},
    ]
    assert result["source_paragraph_count"] == 2
    assert result["target_paragraph_count"] == 2


def test_truncates_to_shorter_side():
    source = ["A", "B", "C"]
    target = ["X", "Y"]
    result = preview_document_pair(source, target)
    assert len(result["pairs"]) == 2
    assert result["source_paragraph_count"] == 3
    assert result["target_paragraph_count"] == 2


def test_empty_inputs_produce_no_pairs():
    result = preview_document_pair([], [])
    assert result["pairs"] == []

from app.llm_alignment import _chunk_text, _parse_alignment_response


def test_chunk_text_empty_returns_no_chunks():
    assert _chunk_text("", "en", 100) == []
    assert _chunk_text("   ", "en", 100) == []


def test_chunk_text_short_text_is_one_chunk():
    text = "First paragraph.\n\nSecond paragraph."
    chunks = _chunk_text(text, "en", 1000)
    assert chunks == ["First paragraph.\n\nSecond paragraph."]


def test_chunk_text_splits_at_paragraph_boundaries_when_over_budget():
    paragraphs = [f"Paragraph number {i}." for i in range(10)]
    text = "\n\n".join(paragraphs)
    # Budget tight enough to force multiple chunks, but each paragraph
    # individually fits comfortably.
    chunks = _chunk_text(text, "en", 60)

    assert len(chunks) > 1
    # No paragraph's text should ever be split across a chunk boundary, and
    # every chunk should respect the budget since no single paragraph here
    # is anywhere near it.
    combined = " ".join(chunks)
    for paragraph in paragraphs:
        assert paragraph in combined
    for chunk in chunks:
        assert len(chunk) <= 60


def test_chunk_text_falls_back_to_sentences_for_oversized_paragraph():
    long_paragraph = " ".join(f"Sentence {i} about the material." for i in range(1, 20))
    chunks = _chunk_text(long_paragraph, "en", 80)

    assert len(chunks) > 1
    combined = " ".join(chunks)
    assert "Sentence 1 about" in combined
    assert "Sentence 19 about" in combined


def test_parse_alignment_response_clean_json():
    content = '[{"source": "Привет", "target": "Hello"}, {"source": "Мир", "target": "World"}]'
    pairs = _parse_alignment_response(content)
    assert pairs == [
        {"source_text": "Привет", "target_text": "Hello"},
        {"source_text": "Мир", "target_text": "World"},
    ]


def test_parse_alignment_response_extracts_json_from_markdown_fence():
    content = 'Sure, here is the alignment:\n```json\n[{"source": "A", "target": "B"}]\n```\nHope that helps!'
    pairs = _parse_alignment_response(content)
    assert pairs == [{"source_text": "A", "target_text": "B"}]


def test_parse_alignment_response_empty_array_is_valid():
    assert _parse_alignment_response("[]") == []


def test_parse_alignment_response_returns_none_on_garbage():
    assert _parse_alignment_response("I cannot help with that.") is None


def test_parse_alignment_response_returns_none_on_wrong_shape():
    # Missing the "target" key entirely.
    content = '[{"source": "A", "translation": "B"}]'
    assert _parse_alignment_response(content) is None


def test_parse_alignment_response_coerces_non_string_values():
    content = '[{"source": "Section 1", "target": 21}]'
    pairs = _parse_alignment_response(content)
    assert pairs == [{"source_text": "Section 1", "target_text": "21"}]

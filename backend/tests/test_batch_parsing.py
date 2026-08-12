from app.translation_service import _parse_numbered_response


def test_parses_well_formed_list():
    text = "1. Первый перевод\n2. Второй перевод\n3. Третий перевод"
    assert _parse_numbered_response(text, 3) == [
        "Первый перевод",
        "Второй перевод",
        "Третий перевод",
    ]


def test_handles_parentheses_style_numbering():
    text = "1) First\n2) Second"
    assert _parse_numbered_response(text, 2) == ["First", "Second"]


def test_returns_none_on_count_mismatch():
    text = "1. Only one line"
    assert _parse_numbered_response(text, 2) is None


def test_returns_none_on_missing_number_in_sequence():
    text = "1. First\n3. Third"
    assert _parse_numbered_response(text, 2) is None


def test_ignores_blank_lines():
    text = "1. First\n\n2. Second\n"
    assert _parse_numbered_response(text, 2) == ["First", "Second"]


def test_ignores_leading_preamble_without_number():
    text = "Sure, here are the translations:\n1. First\n2. Second"
    assert _parse_numbered_response(text, 2) == ["First", "Second"]

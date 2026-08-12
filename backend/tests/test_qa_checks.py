from app.qa_checks import check_segment


def test_clean_translation_has_no_warnings():
    assert check_segment("Настройте параметр timeout.", "Configure the timeout parameter.") == []


def test_empty_translation_is_flagged():
    assert check_segment("Настройте параметр timeout.", "") == ["Пустой перевод"]
    assert check_segment("Настройте параметр timeout.", "   ") == ["Пустой перевод"]


def test_identical_to_source_is_flagged_for_substantial_text():
    warnings = check_segment("This is a real sentence.", "This is a real sentence.")
    assert "Перевод дословно совпадает с оригиналом" in warnings


def test_identical_short_technical_token_is_not_flagged():
    # Legitimate: element symbols, bare numbers, short codes are often
    # identical between languages and should not be treated as suspicious.
    assert check_segment("Mo", "Mo") == []
    assert check_segment("178.29", "178.29") == []
    assert check_segment("E415-21", "E415-21") == []


def test_number_mismatch_is_flagged():
    warnings = check_segment("The tolerance is 178.29 mm.", "Допуск составляет 200 мм.")
    assert "Числа в переводе не совпадают с оригиналом" in warnings


def test_number_with_different_decimal_separator_is_not_flagged():
    # "." (en) vs "," (ru) is a formatting convention difference, not a
    # content mismatch.
    assert check_segment("The value is 178.29 mm.", "Значение составляет 178,29 мм.") == []


def test_matching_numbers_in_different_order_are_not_flagged():
    warnings = check_segment("Width 10 mm, height 20 mm.", "Высота 20 мм, ширина 10 мм.")
    assert "Числа в переводе не совпадают с оригиналом" not in warnings


def test_missing_number_is_flagged():
    warnings = check_segment("Apply 5 coats of primer.", "Нанесите слой грунтовки.")
    assert "Числа в переводе не совпадают с оригиналом" in warnings


def test_empty_source_and_translation_no_number_warning():
    assert check_segment("", "Some translation appeared from nowhere.") == []

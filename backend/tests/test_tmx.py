import pytest

from app.tmx import build_tmx, parse_tmx


def test_build_tmx_produces_well_formed_xml_with_expected_structure():
    entries = [
        {"source_text": "Привет", "target_text": "Hello", "source_lang": "ru", "target_lang": "en"},
        {"source_text": "Мир", "target_text": "World", "source_lang": "ru", "target_lang": "en"},
    ]
    data = build_tmx(entries)

    text = data.decode("utf-8")
    assert "<tmx" in text
    assert text.count("<tu>") == 2
    assert "Привет" in text
    assert "Hello" in text


def test_build_tmx_empty_entries_produces_valid_header():
    data = build_tmx([])
    text = data.decode("utf-8")
    assert "<tmx" in text
    assert "<tu>" not in text


def test_round_trip_build_then_parse_recovers_pairs():
    entries = [
        {"source_text": "Настройте параметр timeout.", "target_text": "Configure the timeout parameter.", "source_lang": "ru", "target_lang": "en"},
        {"source_text": "Второй абзац.", "target_text": "Second paragraph.", "source_lang": "ru", "target_lang": "en"},
    ]
    data = build_tmx(entries)
    pairs = parse_tmx(data, "ru", "en")

    assert pairs == [
        {"source_text": "Настройте параметр timeout.", "target_text": "Configure the timeout parameter."},
        {"source_text": "Второй абзац.", "target_text": "Second paragraph."},
    ]


def test_parse_tmx_matches_language_tags_case_and_region_insensitively():
    data = """<?xml version="1.0" encoding="UTF-8"?>
    <tmx version="1.4">
      <header creationtool="x" creationtoolversion="1" datatype="plaintext" segtype="sentence" adminlang="en" srclang="RU-ru" o-tmf="x"/>
      <body>
        <tu>
          <tuv xml:lang="RU-ru"><seg>Тест</seg></tuv>
          <tuv xml:lang="en-US"><seg>Test</seg></tuv>
        </tu>
      </body>
    </tmx>""".encode("utf-8")
    pairs = parse_tmx(data, "ru", "en")
    assert pairs == [{"source_text": "Тест", "target_text": "Test"}]


def test_parse_tmx_skips_translation_units_missing_requested_language():
    data = """<?xml version="1.0" encoding="UTF-8"?>
    <tmx version="1.4">
      <header creationtool="x" creationtoolversion="1" datatype="plaintext" segtype="sentence" adminlang="en" srclang="ru" o-tmf="x"/>
      <body>
        <tu>
          <tuv xml:lang="ru"><seg>Только русский и французский</seg></tuv>
          <tuv xml:lang="fr"><seg>Seulement russe et francais</seg></tuv>
        </tu>
        <tu>
          <tuv xml:lang="ru"><seg>Русский и английский</seg></tuv>
          <tuv xml:lang="en"><seg>Russian and English</seg></tuv>
        </tu>
      </body>
    </tmx>""".encode("utf-8")
    pairs = parse_tmx(data, "ru", "en")
    assert pairs == [{"source_text": "Русский и английский", "target_text": "Russian and English"}]


def test_parse_tmx_rejects_malformed_xml():
    with pytest.raises(ValueError, match="TMX"):
        parse_tmx(b"not even xml", "ru", "en")

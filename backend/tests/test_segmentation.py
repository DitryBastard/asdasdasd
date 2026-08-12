from app.segmentation import split_paragraphs, split_sentences


def test_split_sentences_russian():
    text = "Это первое предложение. Это второе предложение! А это третье?"
    assert split_sentences(text, "ru") == [
        "Это первое предложение.",
        "Это второе предложение!",
        "А это третье?",
    ]


def test_split_sentences_english():
    text = "This is sentence one. This is sentence two."
    assert len(split_sentences(text, "en")) == 2


def test_split_sentences_empty_text():
    assert split_sentences("   ", "en") == []


def test_split_sentences_unknown_language_falls_back():
    # Not a language pysbd ships rules for; should not raise.
    sentences = split_sentences("Hello there. How are you?", "xx")
    assert len(sentences) == 2


def test_split_paragraphs():
    text = "First paragraph.\n\nSecond paragraph.\n\n\nThird."
    assert split_paragraphs(text) == ["First paragraph.", "Second paragraph.", "Third."]


def test_split_paragraphs_empty_text():
    assert split_paragraphs("   \n\n  ") == []

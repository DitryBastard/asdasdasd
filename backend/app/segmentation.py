import re

import pysbd

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
_segmenters: dict[str, pysbd.Segmenter] = {}


def _get_segmenter(lang: str) -> pysbd.Segmenter:
    if lang not in _segmenters:
        try:
            _segmenters[lang] = pysbd.Segmenter(language=lang, clean=False)
        except Exception:
            # pysbd only ships rules for a fixed set of languages; fall back
            # to the generic English ruleset for anything else rather than
            # failing the whole request.
            _segmenters[lang] = pysbd.Segmenter(language="en", clean=False)
    return _segmenters[lang]


def split_sentences(text: str, lang: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in _get_segmenter(lang).segment(text) if s.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]

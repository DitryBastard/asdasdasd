"""Rebuild an uploaded .docx with translated text, keeping its formatting.

Scope, deliberately: formatting is preserved at the *paragraph* level -
style (heading, list, ...), alignment, and the run formatting (font, bold,
italic, size, color) of the paragraph's first run, which is then applied to
the whole translated paragraph. Formatting that varies run-to-run *within*
a paragraph (e.g. one bold word in the middle of a sentence) is not
preserved: there is no general way to know which span of a *translated*
sentence corresponds to a formatted span of the *original* once word order
and count have changed - the same simplification every mainstream CAT tool
makes for anything beyond simple, position-stable inline tags.
"""

import io

from docx import Document

from .document_parser import iter_docx_paragraphs


def build_translated_docx(original_bytes: bytes, translations: dict[str, str]) -> bytes:
    """translations maps each original paragraph's stripped text to its
    translation. Paragraphs not found in the map (blank spacer paragraphs,
    or anything that failed to translate) are left untouched.
    """
    document = Document(io.BytesIO(original_bytes))
    for paragraph in iter_docx_paragraphs(document):
        original_text = paragraph.text.strip()
        if not original_text:
            continue
        translated = translations.get(original_text)
        if translated is None:
            continue
        _replace_paragraph_text(paragraph, translated)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _replace_paragraph_text(paragraph, new_text: str) -> None:
    if not paragraph.runs:
        paragraph.add_run(new_text)
        return
    paragraph.runs[0].text = new_text
    for run in paragraph.runs[1:]:
        run.text = ""


def translations_by_paragraph(paragraphs: list[str], segments: list[dict]) -> dict[str, str]:
    """Join sentence-level translation segments back into one translated
    string per original paragraph, keyed by that paragraph's original text -
    the lookup build_translated_docx needs. `segments` is the same
    paragraph_index-tagged segment list translation_service.translate_text
    returns.
    """
    grouped: dict[int, list[str]] = {}
    for segment in segments:
        grouped.setdefault(segment["paragraph_index"], []).append(segment["translation"])
    return {
        paragraphs[index]: " ".join(translations)
        for index, translations in grouped.items()
        if index < len(paragraphs)
    }

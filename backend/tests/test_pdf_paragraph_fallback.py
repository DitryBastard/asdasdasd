"""Regression coverage for the 823-vs-319 paragraph explosion reported on a
real ISO/ASTM-style standard: a page of densely-set text with no blank-line
paragraph breaks used to fall back to one paragraph per physical (wrapped)
line, shredding a handful of real paragraphs into hundreds of fragments and
wrecking translation quality on the /api/translate/document(/formatted)
endpoints, which still use extract_paragraphs_pdf's paragraph list. (The
memory-alignment preview no longer pre-splits into paragraphs at all - see
app/llm_alignment.py - so this fallback logic doesn't apply there anymore.)
"""

import io

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

from app.document_parser import extract_paragraphs_pdf


def _build_dense_pdf() -> bytes:
    # One long paragraph reportlab must wrap across many physical lines,
    # with no blank line anywhere - exactly the shape that used to trigger
    # the harmful per-line fallback.
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    long_text = " ".join(f"Sentence number {i} about the material composition." for i in range(1, 40))
    doc.build([Paragraph(long_text, styles["Normal"])])
    return buffer.getvalue()


def test_extract_paragraphs_pdf_does_not_shred_dense_text_line_by_line():
    paragraphs = extract_paragraphs_pdf(_build_dense_pdf())

    assert len(paragraphs) <= 2
    combined = " ".join(paragraphs)
    assert "Sentence number 1 about" in combined
    assert "Sentence number 39 about" in combined
